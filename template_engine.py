import re

class TemplateEngine:
    def __init__(self):
        self.tags = {
            "for": re.compile(r"\{% for (\w+) in (\w+) %\}"),
            "endfor": re.compile(r"\{% endfor %\}"),
            "if": re.compile(r"\{% if (.+) %\}"),  # Basic if condition
            "endif": re.compile(r"\{% endif %\}"),
            "variable": re.compile(r"\{\{ (\w+) \}\}"),
        }

    def render(self, template, context):
        tokens = self.tokenize(template)
        return self.parse(tokens, context)

    def tokenize(self, template):
        parts = re.split(r"(\{%.*?%\}|\{\{.*?\}\})", template)  # Split by tags
        return [p.strip() for p in parts if p.strip()]  # Remove empty strings

    def parse(self, tokens, context):
        output = ""
        loop_vars = []  # Stack to track loop variables
        conditional_stack = []  # Stack to track if conditions

        for token in tokens:
            if token in self.tags and token == "{% endfor %}":
                loop_vars.pop()  # Exit loop
            elif token in self.tags and token == "{% endif %}":
                conditional_stack.pop()
            elif token in self.tags:
                match = self.tags["for"].match(token)
                if match:
                    loop_var, iterable_name = match.groups()
                    iterable = context.get(iterable_name)

                    if isinstance(iterable, list) or isinstance(iterable, tuple): #handles lists and tuples
                        loop_vars.append((loop_var, iterable))  # Enter loop
                        for item in iterable:
                            context[loop_var] = item  # Set loop variable in context
                            output += self.parse(tokens[tokens.index(token) + 1:tokens.index("{% endfor %}")], context)
                            del context[loop_var] #cleanup
                    else:
                        raise ValueError(f"Iterable {iterable_name} must be a list or tuple")

                match = self.tags["if"].match(token)
                if match:
                    condition = match.group(1)
                    try:
                        result = eval(condition, {}, context) #evaluates the conditions
                        conditional_stack.append(result)
                        if result:
                            output += self.parse(tokens[tokens.index(token) + 1:tokens.index("{% endif %}")], context)
                    except Exception as e:
                        raise ValueError(f"Invalid if condition: {condition}. Error: {e}")
            else:
                match = self.tags["variable"].match(token)
                if match:
                    variable_name = match.group(1)
                    output += str(context.get(variable_name, ""))  # Resolve variable
                else:
                    output += token  # Text outside tags

        return output

# Example usage:
template = """
<h1>Hello, {{ name }}!</h1>

<ul>
{% for item in items %}
    <li>{{ item }}</li>
{% endfor %}
</ul>

{% if show_message %}
<p>This is a conditional message.</p>
{% endif %}

<ul>
{% for user in users %}
    <li>{{ user.name }} ({{ user.age }})</li>
    <ul>
    {% for hobby in user.hobbies %}
        <li>{{ hobby }}</li>
    {% endfor %}
    </ul>
{% endfor %}
</ul>
"""

context = {
    "name": "World",
    "items": ["apple", "banana", "cherry"],
    "show_message": True,
    "users": [
        {"name": "Alice", "age": 30, "hobbies": ["reading", "coding"]},
        {"name": "Bob", "age": 25, "hobbies": ["hiking", "gaming"]},
    ],
}

engine = TemplateEngine()
rendered_html = engine.render(template, context)
print(rendered_html)