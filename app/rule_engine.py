from typing import Any


def evaluate_rule(field_value: Any, operator: str, rule_value: Any) -> bool:
    if operator == "GREATER_THAN":
        return field_value > rule_value
    if operator == "LESS_THAN":
        return field_value < rule_value
    if operator == "EQUALS":
        return field_value == rule_value
    if operator == "NOT_EQUALS":
        return field_value != rule_value
    if operator == "GREATER_THAN_OR_EQUAL":
        return field_value >= rule_value
    if operator == "LESS_THAN_OR_EQUAL":
        return field_value <= rule_value

    raise ValueError(f"Unsupported operator: {operator}")


def evaluate_rule_group(rule_group: dict, user_data: dict) -> bool:
    operator = rule_group.get("operator")
    rules = rule_group.get("rules", [])

    results = []

    for rule in rules:
        field = rule["field"]
        rule_operator = rule["operator"]
        rule_value = rule["value"]

        field_value = user_data.get(field)

        if field_value is None:
            return False

        results.append(evaluate_rule(field_value, rule_operator, rule_value))

    if operator == "AND":
        return all(results)
    if operator == "OR":
        return any(results)

    raise ValueError(f"Unsupported group operator: {operator}")