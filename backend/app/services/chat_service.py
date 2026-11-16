"""HomeCare AI Assistant: LLM-backed with a rule-based natural-language fallback."""
import re
import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Appliance, ChatHistory, MaintenanceSchedule, ReportedIssue, User
from app.models.enums import SERVICE_INTERVAL_DAYS
from app.services import knowledge_base as kb
from app.services.llm_client import chat_completion

SYSTEM_PROMPT = """You are "HomeCare AI Assistant", a household appliance maintenance assistant inside the
Smart Household Maintenance Manager app. Help the user maintain their home appliances.
Rules:
- Use the user's registered appliance data (provided below) when relevant; refer to appliances by name.
- Give practical, safe troubleshooting steps a homeowner can do. Never suggest opening sealed electrical,
  gas/refrigerant, or high-voltage components (e.g. microwave internals).
- Present diagnoses as *possible* causes; never state uncertain diagnoses as facts.
- Recommend a qualified professional when there is a safety risk or the fix needs specialist work.
- Health scores come from a model trained on synthetic data: describe them as maintenance-priority estimates.
- Stay on household maintenance topics; politely decline unrelated requests.
- Be concise; use short paragraphs or bullet lists (markdown is supported)."""


def _age(a: Appliance) -> str:
    start = a.installation_date or a.purchase_date
    if not start:
        return "unknown age"
    return f"{(date.today() - start).days / 365.25:.1f} yrs old"


def build_context(db: Session, user: User) -> tuple[list[Appliance], str]:
    appliances = db.scalars(select(Appliance).where(Appliance.user_id == user.id)).all()
    if not appliances:
        return [], "The user has not registered any appliances yet."
    lines = ["User's registered appliances:"]
    for a in appliances:
        open_issues = [i for i in a.issues if i.status != "Resolved"]
        issue_txt = "; ".join(f"{i.problem_category} ({i.severity})" for i in open_issues) or "none"
        lines.append(
            f"- {a.name} [{a.category}, {a.brand or 'unknown brand'}], {_age(a)}, usage {a.usage_frequency}, "
            f"condition {a.condition}, last service {a.last_service_date or 'never recorded'}, "
            f"health {a.health_score if a.health_score is not None else 'n/a'}/100, risk {a.risk_level or 'n/a'}, "
            f"recommended service {a.next_service_date or 'n/a'}, warranty until {a.warranty_expiry or 'unknown'}, "
            f"open issues: {issue_txt}"
        )
    upcoming = db.scalars(select(MaintenanceSchedule).where(
        MaintenanceSchedule.user_id == user.id,
        MaintenanceSchedule.status.in_(["Pending", "Scheduled", "In Progress"])
    ).order_by(MaintenanceSchedule.scheduled_at).limit(10)).all()
    if upcoming:
        lines.append("Upcoming maintenance tasks:")
        lines += [f"- {s.scheduled_at:%Y-%m-%d}: {s.title} ({s.appliance.name}, {s.status})" for s in upcoming]
    lines.append(f"Today's date: {date.today().isoformat()}")
    return appliances, "\n".join(lines)


# ---------------------------------------------------------------- rule-based NLU

def _norm(text: str) -> str:
    return " " + re.sub(r"\s+", " ", text.lower()) + " "


def detect_symptom(text: str) -> str | None:
    t = _norm(text)
    best, best_len = None, 0
    for symptom, words in kb.SYMPTOM_KEYWORDS.items():
        for w in words:
            if w in t and len(w) > best_len:
                best, best_len = symptom, len(w)
    return best


def detect_category(text: str) -> str | None:
    t = _norm(text)
    for cat, words in kb.CATEGORY_KEYWORDS.items():
        if any(w in t for w in words):
            return cat
    return None


def _match_appliance(text: str, appliances: list[Appliance]) -> Appliance | None:
    t = _norm(text)
    for a in appliances:
        if a.name.lower() in t:
            return a
    cat = detect_category(text)
    if cat:
        matches = [a for a in appliances if a.category == cat]
        if matches:
            return sorted(matches, key=lambda a: a.health_score if a.health_score is not None else 100)[0]
    return None


def _risk_rank(a: Appliance) -> tuple:
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, None: 4}
    return order.get(a.risk_level, 4), a.health_score if a.health_score is not None else 100


def rule_based_reply(db: Session, user: User, message: str, appliances: list[Appliance]) -> str:
    t = _norm(message)
    today = date.today()

    if re.search(r"\b(hi|hello|hey|namaste|good (morning|evening|afternoon))\b", t) and len(t) < 30:
        return (f"Hello {user.full_name.split()[0]}! I'm the HomeCare AI Assistant. Ask me about appliance problems, "
                "servicing schedules, energy saving, or which appliance needs attention first.")

    # Which appliance needs immediate maintenance?
    if re.search(r"(which|what).*(appliance|device).*(immediate|urgent|attention|first|priority|risk|need)", t) or \
            "requires immediate" in t or "most urgent" in t or "highest risk" in t:
        if not appliances:
            return "You haven't registered any appliances yet. Add them under **My Appliances** and I can rank them by risk."
        ranked = sorted(appliances, key=_risk_rank)
        urgent = [a for a in ranked if a.risk_level in ("High", "Critical")]
        lines = []
        if urgent:
            lines.append("These appliances need attention soonest, based on their latest health assessment:")
            for a in urgent:
                lines.append(f"- **{a.name}** — {a.risk_level} risk, health {a.health_score:.0f}/100, "
                             f"service recommended by {a.next_service_date:%d %b %Y}")
        else:
            top = ranked[0]
            lines.append("None of your appliances are at High or Critical risk right now. 👍")
            if top.health_score is not None:
                lines.append(f"The lowest health score is **{top.name}** ({top.health_score:.0f}/100, "
                             f"{top.risk_level} risk) — next service suggested by {top.next_service_date:%d %b %Y}.")
        lines.append("\n_Health scores are maintenance-priority estimates from a model trained on synthetic data, "
                     "not guaranteed failure predictions._")
        return "\n".join(lines)

    # Maintenance tasks this month
    if re.search(r"(this|current|next) month", t) or ("tasks" in t and "month" in t) or "to do list" in t:
        start = today.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1)
        tasks = db.scalars(select(MaintenanceSchedule).where(
            MaintenanceSchedule.user_id == user.id,
            MaintenanceSchedule.status.in_(["Pending", "Scheduled", "In Progress"]),
            MaintenanceSchedule.scheduled_at >= datetime.combine(start, datetime.min.time()),
            MaintenanceSchedule.scheduled_at < datetime.combine(end, datetime.min.time()),
        ).order_by(MaintenanceSchedule.scheduled_at)).all()
        due = [a for a in appliances if a.next_service_date and a.next_service_date < end]
        lines = [f"**Maintenance plan for {today:%B %Y}:**"]
        if tasks:
            lines.append("Scheduled tasks:")
            lines += [f"- {s.scheduled_at:%d %b}: {s.title} — {s.appliance.name} ({s.status})" for s in tasks]
        scheduled_ids = {s.appliance_id for s in tasks}
        extra = [a for a in due if a.id not in scheduled_ids]
        if extra:
            lines.append("Recommended by the predictive model (not yet scheduled):")
            lines += [f"- {a.name}: service by {a.next_service_date:%d %b} ({a.risk_level} risk)" for a in extra]
        lines.append("Routine monthly checks:")
        lines += ["- Clean AC filters (every 2–4 weeks in summer)", "- Clean the washing machine drain filter and door seal",
                  "- Wipe fridge door gaskets and check the temperature setting",
                  "- Check the water purifier's taste and flow; note filter-change dates"]
        if not tasks and not extra:
            lines.insert(1, "No tasks are scheduled this month and none of your appliances are due.")
        return "\n".join(lines)

    symptom = detect_symptom(message)
    target = _match_appliance(message, appliances)
    category = target.category if target else detect_category(message)

    # Energy saving
    if symptom == "power_consumption" or "reduce electricity" in t:
        e = kb.GENERAL_BY_SYMPTOM["power_consumption"]
        lines = ["**Ways to reduce electricity consumption:**"] + [f"- {s}" for s in e["steps"]]
        poor = [a for a in appliances if a.condition in ("Fair", "Poor") or (a.risk_level in ("High", "Critical"))]
        if poor:
            lines.append("\nIn your home, these may be drawing extra power due to wear or overdue servicing: "
                         + ", ".join(f"**{a.name}**" for a in poor) + ". Servicing them may improve efficiency.")
        return "\n".join(lines)

    # When should I service X?
    if re.search(r"\b(when|how often)\b.*\b(service|servicing|maintain|maintenance|clean)\b", t):
        if not category:
            return ("Typical servicing intervals: AC every 6 months, water purifier filters every 3–6 months, "
                    "washing machine every 6 months, fridge/geyser/microwave yearly, TV every 2 years. "
                    "Tell me which appliance you mean for a specific recommendation.")
        interval = SERVICE_INTERVAL_DAYS.get(category, 365)
        months = round(interval / 30)
        lines = [f"A {category.lower()} should generally be serviced about every **{months} months**."]
        if target:
            lines.append(f"Your **{target.name}** was last serviced on "
                         f"{target.last_service_date:%d %b %Y}." if target.last_service_date else
                         f"I have no service record for your **{target.name}**.")
            if target.next_service_date:
                lines.append(f"Based on its age, usage and history, the next service is recommended by "
                             f"**{target.next_service_date:%d %b %Y}** (current risk: {target.risk_level}).")
            lines.append("You can book it from the **Maintenance Scheduler**.")
        if category == "Air Conditioner":
            lines.append("Tip: service before summer starts and clean filters every 2–4 weeks during heavy use.")
        return "\n".join(lines)

    # Troubleshooting
    if symptom and symptom != "power_consumption":
        if not category:
            return (f"I can help with that. Which appliance is it — fridge, AC, washing machine, water purifier, "
                    f"geyser, microwave or TV? Some possible general causes:\n\n"
                    + kb.format_troubleshooting("the appliance", "Other", symptom))
        label = f"your {target.name}" if target else f"a {category.lower()}"
        reply = kb.format_troubleshooting(label, category, symptom)
        if target:
            extra = []
            if target.risk_level in ("High", "Critical"):
                extra.append(f"Note: {target.name} is currently assessed at **{target.risk_level} risk** "
                             f"(health {target.health_score:.0f}/100), so professional servicing is advisable.")
            if target.warranty_expiry and target.warranty_expiry >= today:
                extra.append(f"It is still under warranty until {target.warranty_expiry:%d %b %Y} — "
                             "contact the brand's service centre before paying for repairs.")
            if extra:
                reply += "\n\n" + "\n".join(extra)
        reply += "\n\nYou can log this under **Report an Issue** so it is factored into the risk assessment."
        return reply

    # Status of a specific appliance
    if target and re.search(r"(status|health|condition|how is|how's|risk|score)", t):
        return (f"**{target.name}** ({target.category}): health {target.health_score or 0:.0f}/100, "
                f"{target.risk_level or 'unassessed'} risk, condition {target.condition}, {_age(target)}. "
                f"Next service recommended by {target.next_service_date:%d %b %Y}." if target.next_service_date else
                f"**{target.name}** has not been assessed yet. Run a prediction from **Predictive Maintenance**.")

    if "warranty" in t:
        items = [a for a in appliances if a.warranty_expiry]
        if not items:
            return "None of your appliances have a warranty expiry date recorded."
        lines = ["**Warranty status:**"]
        for a in sorted(items, key=lambda a: a.warranty_expiry):
            state = "active" if a.warranty_expiry >= today else "expired"
            lines.append(f"- {a.name}: {state} (until {a.warranty_expiry:%d %b %Y})")
        return "\n".join(lines)

    return ("I'm the HomeCare AI Assistant (running in offline rule-based mode). I can help with:\n"
            "- Troubleshooting (e.g. *Why is my washing machine leaking?*)\n"
            "- Service timing (e.g. *When should I service my AC?*)\n"
            "- Priorities (e.g. *Which appliance requires immediate maintenance?*)\n"
            "- Monthly plans (e.g. *What maintenance tasks should I do this month?*)\n"
            "- Energy saving (e.g. *How can I reduce electricity consumption?*)\n"
            "Could you rephrase your question with the appliance and the symptom?")


# ---------------------------------------------------------------- public API

def answer(db: Session, user: User, message: str, session_id: str | None) -> tuple[str, ChatHistory]:
    session_id = session_id or uuid.uuid4().hex
    appliances, context = build_context(db, user)

    history = db.scalars(select(ChatHistory).where(
        ChatHistory.user_id == user.id, ChatHistory.session_id == session_id
    ).order_by(ChatHistory.created_at.desc(), ChatHistory.id.desc()).limit(10)).all()[::-1]

    db.add(ChatHistory(user_id=user.id, session_id=session_id, role="user", message=message))
    db.flush()

    msgs = [{"role": h.role, "content": h.message} for h in history]
    msgs.append({"role": "user", "content": message})
    reply = chat_completion(f"{SYSTEM_PROMPT}\n\n{context}", msgs)
    source = "llm"
    if not reply:
        reply = rule_based_reply(db, user, message, appliances)
        source = "rules"

    bot = ChatHistory(user_id=user.id, session_id=session_id, role="assistant", message=reply, source=source)
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return session_id, bot


def issue_suggestions(appliance: Appliance, problem_category: str, description: str, severity: str) -> tuple[str, str]:
    """AI troubleshooting suggestions for a reported issue. Returns (text, source)."""
    symptom = kb.PROBLEM_CATEGORY_TO_SYMPTOM.get(problem_category, "general")
    if symptom == "general":
        symptom = detect_symptom(description) or "general"
    prompt = (f"Appliance: {appliance.name} ({appliance.category}, {appliance.brand or 'unknown brand'}, "
              f"{_age(appliance)}, condition {appliance.condition}). Problem category: {problem_category}. "
              f"Severity: {severity}. Description: {description}\n"
              "Give: possible causes (as possibilities), safe troubleshooting steps, and when to call a professional.")
    text = chat_completion(SYSTEM_PROMPT, [{"role": "user", "content": prompt}], max_tokens=600)
    if text:
        return text, "llm"
    return kb.format_troubleshooting(f"your {appliance.name}", appliance.category, symptom, severity), "rules"
