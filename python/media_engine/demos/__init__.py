"""
Interactive HTML Demos for Media Engine

Supports embedding interactive demos in documentation:
- Code playgrounds (HTML/CSS/JS)
- Interactive diagrams
- Data visualizations
- Form demos
- API explorers

Demos are defined as YAML files and rendered to self-contained HTML.
"""

import hashlib
import html
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class DemoType(str, Enum):
    """Types of interactive demos."""

    CODE_PLAYGROUND = "code_playground"  # HTML/CSS/JS editor
    DATA_VIZ = "data_viz"  # Charts and graphs
    INTERACTIVE_DIAGRAM = "interactive_diagram"  # Clickable diagrams
    FORM_DEMO = "form_demo"  # Form with validation
    API_EXPLORER = "api_explorer"  # API endpoint tester
    CALCULATOR = "calculator"  # Interactive calculator
    TIMELINE = "timeline"  # Interactive timeline
    COMPARISON = "comparison"  # Side-by-side comparison
    QUIZ = "quiz"  # Interactive quiz


@dataclass
class DemoConfig:
    """Configuration for an interactive demo."""

    id: str
    type: DemoType
    title: str
    description: str = ""
    width: str = "100%"
    height: str = "400px"
    theme: str = "light"
    editable: bool = True
    autorun: bool = True
    data: dict = field(default_factory=dict)


class DemoRenderer:
    """Renders demo configurations to HTML."""

    def __init__(self, theme=None):
        self.theme = theme
        self._get_colors()

    def _get_colors(self):
        """Extract colors from theme."""
        if self.theme:
            self.primary = self.theme.colors.get("primary", "#2c2522")
            self.accent = self.theme.colors.get("accent", "#0066cc")
            self.bg = self.theme.colors.get("background", "#ffffff")
            self.text = self.theme.colors.get("text", "#2c2522")
        else:
            self.primary = "#2c2522"
            self.accent = "#0066cc"
            self.bg = "#ffffff"
            self.text = "#2c2522"

    def render(self, config: DemoConfig) -> str:
        """Render demo to HTML."""
        renderer_map = {
            DemoType.CODE_PLAYGROUND: self._render_code_playground,
            DemoType.DATA_VIZ: self._render_data_viz,
            DemoType.INTERACTIVE_DIAGRAM: self._render_diagram,
            DemoType.FORM_DEMO: self._render_form,
            DemoType.API_EXPLORER: self._render_api_explorer,
            DemoType.CALCULATOR: self._render_calculator,
            DemoType.TIMELINE: self._render_timeline,
            DemoType.COMPARISON: self._render_comparison,
            DemoType.QUIZ: self._render_quiz,
        }

        renderer = renderer_map.get(config.type, self._render_generic)
        return renderer(config)

    def _base_styles(self, config: DemoConfig) -> str:
        """Generate base CSS styles."""
        return f"""
        <style>
            .demo-container-{config.id} {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                overflow: hidden;
                background: {self.bg};
                color: {self.text};
                width: {config.width};
                margin: 1em 0;
            }}
            .demo-header-{config.id} {{
                background: {self.primary};
                color: white;
                padding: 0.75em 1em;
                font-weight: 600;
            }}
            .demo-body-{config.id} {{
                padding: 1em;
                min-height: {config.height};
            }}
            .demo-btn {{
                background: {self.accent};
                color: white;
                border: none;
                padding: 0.5em 1em;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.9em;
            }}
            .demo-btn:hover {{
                opacity: 0.9;
            }}
            .demo-input {{
                padding: 0.5em;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 0.9em;
            }}
            .demo-output {{
                background: #f5f5f5;
                padding: 1em;
                border-radius: 4px;
                font-family: monospace;
                white-space: pre-wrap;
                margin-top: 1em;
            }}
        </style>
        """

    def _render_code_playground(self, config: DemoConfig) -> str:
        """Render an HTML/CSS/JS code playground."""
        html_code = html.escape(config.data.get("html", "<h1>Hello World</h1>"))
        css_code = html.escape(config.data.get("css", "h1 { color: blue; }"))
        js_code = html.escape(config.data.get("js", "console.log('Ready!');"))

        return f"""
        {self._base_styles(config)}
        <div class="demo-container-{config.id}">
            <div class="demo-header-{config.id}">{html.escape(config.title)}</div>
            <div class="demo-body-{config.id}">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1em;">
                    <div>
                        <div style="margin-bottom: 0.5em;">
                            <label style="font-weight: 600;">HTML</label>
                            <textarea id="html-{config.id}" class="demo-input" style="width: 100%; height: 100px; font-family: monospace;">{html_code}</textarea>
                        </div>
                        <div style="margin-bottom: 0.5em;">
                            <label style="font-weight: 600;">CSS</label>
                            <textarea id="css-{config.id}" class="demo-input" style="width: 100%; height: 80px; font-family: monospace;">{css_code}</textarea>
                        </div>
                        <div style="margin-bottom: 0.5em;">
                            <label style="font-weight: 600;">JavaScript</label>
                            <textarea id="js-{config.id}" class="demo-input" style="width: 100%; height: 80px; font-family: monospace;">{js_code}</textarea>
                        </div>
                        <button class="demo-btn" onclick="runDemo_{config.id}()">Run</button>
                    </div>
                    <div>
                        <label style="font-weight: 600;">Output</label>
                        <iframe id="output-{config.id}" style="width: 100%; height: 280px; border: 1px solid #ddd; border-radius: 4px; background: white;"></iframe>
                    </div>
                </div>
            </div>
        </div>
        <script>
            function runDemo_{config.id}() {{
                const htmlCode = document.getElementById('html-{config.id}').value;
                const cssCode = document.getElementById('css-{config.id}').value;
                const jsCode = document.getElementById('js-{config.id}').value;
                const iframe = document.getElementById('output-{config.id}');
                const doc = iframe.contentDocument || iframe.contentWindow.document;
                doc.open();
                doc.write('<style>' + cssCode + '</style>' + htmlCode + '<script>' + jsCode + '<\\/script>');
                doc.close();
            }}
            {"runDemo_" + config.id + "();" if config.autorun else ""}
        </script>
        """

    def _render_data_viz(self, config: DemoConfig) -> str:
        """Render a data visualization demo."""
        chart_type = config.data.get("chart_type", "bar")
        labels = json.dumps(config.data.get("labels", ["A", "B", "C", "D"]))
        values = json.dumps(config.data.get("values", [10, 20, 15, 25]))
        chart_title = html.escape(config.data.get("chart_title", ""))

        return f"""
        {self._base_styles(config)}
        <div class="demo-container-{config.id}">
            <div class="demo-header-{config.id}">{html.escape(config.title)}</div>
            <div class="demo-body-{config.id}">
                <canvas id="chart-{config.id}" style="width: 100%; height: {config.height};"></canvas>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            (function() {{
                const ctx = document.getElementById('chart-{config.id}').getContext('2d');
                new Chart(ctx, {{
                    type: '{chart_type}',
                    data: {{
                        labels: {labels},
                        datasets: [{{
                            label: '{chart_title}',
                            data: {values},
                            backgroundColor: '{self.accent}80',
                            borderColor: '{self.accent}',
                            borderWidth: 2
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false
                    }}
                }});
            }})();
        </script>
        """

    def _render_diagram(self, config: DemoConfig) -> str:
        """Render an interactive diagram."""
        nodes = config.data.get("nodes", [])
        connections = config.data.get("connections", [])

        nodes_html = ""
        for node in nodes:
            x = node.get("x", 50)
            y = node.get("y", 50)
            label = html.escape(node.get("label", ""))
            node_id = node.get("id", "")
            desc = html.escape(node.get("description", ""))

            nodes_html += f"""
            <div class="diagram-node" data-id="{node_id}"
                 style="left: {x}px; top: {y}px;"
                 onclick="showInfo_{config.id}('{node_id}', '{desc}')">
                {label}
            </div>
            """

        return f"""
        {self._base_styles(config)}
        <style>
            .diagram-canvas-{config.id} {{
                position: relative;
                background: #f9f9f9;
                min-height: {config.height};
            }}
            .diagram-node {{
                position: absolute;
                background: {self.accent};
                color: white;
                padding: 0.5em 1em;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.9em;
                transition: transform 0.2s;
            }}
            .diagram-node:hover {{
                transform: scale(1.05);
            }}
            .diagram-info-{config.id} {{
                background: #fff;
                border: 1px solid #ddd;
                padding: 1em;
                border-radius: 4px;
                margin-top: 1em;
            }}
        </style>
        <div class="demo-container-{config.id}">
            <div class="demo-header-{config.id}">{html.escape(config.title)}</div>
            <div class="demo-body-{config.id}">
                <div class="diagram-canvas-{config.id}">
                    {nodes_html}
                </div>
                <div class="diagram-info-{config.id}" id="info-{config.id}">
                    Click on a node to see details.
                </div>
            </div>
        </div>
        <script>
            function showInfo_{config.id}(nodeId, description) {{
                document.getElementById('info-{config.id}').innerHTML =
                    '<strong>' + nodeId + '</strong><br>' + description;
            }}
        </script>
        """

    def _render_form(self, config: DemoConfig) -> str:
        """Render a form demo with validation."""
        fields = config.data.get("fields", [])

        fields_html = ""
        for field in fields:
            name = field.get("name", "")
            label = html.escape(field.get("label", name))
            field_type = field.get("type", "text")
            required = "required" if field.get("required", False) else ""
            pattern = f'pattern="{field.get("pattern", "")}"' if field.get("pattern") else ""

            fields_html += f"""
            <div style="margin-bottom: 1em;">
                <label style="display: block; font-weight: 600; margin-bottom: 0.25em;">{label}</label>
                <input type="{field_type}" name="{name}" class="demo-input"
                       style="width: 100%;" {required} {pattern}>
            </div>
            """

        return f"""
        {self._base_styles(config)}
        <div class="demo-container-{config.id}">
            <div class="demo-header-{config.id}">{html.escape(config.title)}</div>
            <div class="demo-body-{config.id}">
                <form id="form-{config.id}" onsubmit="return submitForm_{config.id}(event)">
                    {fields_html}
                    <button type="submit" class="demo-btn">Submit</button>
                </form>
                <div class="demo-output" id="result-{config.id}" style="display: none;"></div>
            </div>
        </div>
        <script>
            function submitForm_{config.id}(e) {{
                e.preventDefault();
                const form = document.getElementById('form-{config.id}');
                const data = new FormData(form);
                const result = {{}};
                data.forEach((value, key) => result[key] = value);
                document.getElementById('result-{config.id}').style.display = 'block';
                document.getElementById('result-{config.id}').textContent =
                    'Form submitted:\\n' + JSON.stringify(result, null, 2);
                return false;
            }}
        </script>
        """

    def _render_api_explorer(self, config: DemoConfig) -> str:
        """Render an API explorer demo."""
        endpoints = config.data.get("endpoints", [])
        base_url = config.data.get("base_url", "")

        options = ""
        for ep in endpoints:
            method = ep.get("method", "GET")
            path = ep.get("path", "/")
            options += f'<option value="{method}|{path}">{method} {path}</option>'

        return f"""
        {self._base_styles(config)}
        <div class="demo-container-{config.id}">
            <div class="demo-header-{config.id}">{html.escape(config.title)}</div>
            <div class="demo-body-{config.id}">
                <div style="margin-bottom: 1em;">
                    <label style="font-weight: 600;">Endpoint</label>
                    <select id="endpoint-{config.id}" class="demo-input" style="width: 100%;">
                        {options}
                    </select>
                </div>
                <div style="margin-bottom: 1em;">
                    <label style="font-weight: 600;">Request Body (JSON)</label>
                    <textarea id="body-{config.id}" class="demo-input"
                              style="width: 100%; height: 80px; font-family: monospace;">{{}}</textarea>
                </div>
                <button class="demo-btn" onclick="sendRequest_{config.id}()">Send Request</button>
                <div class="demo-output" id="response-{config.id}">Response will appear here...</div>
            </div>
        </div>
        <script>
            async function sendRequest_{config.id}() {{
                const select = document.getElementById('endpoint-{config.id}');
                const [method, path] = select.value.split('|');
                const body = document.getElementById('body-{config.id}').value;
                const output = document.getElementById('response-{config.id}');

                output.textContent = 'Sending request...';

                try {{
                    const options = {{
                        method: method,
                        headers: {{ 'Content-Type': 'application/json' }}
                    }};
                    if (method !== 'GET' && body) {{
                        options.body = body;
                    }}

                    const response = await fetch('{base_url}' + path, options);
                    const data = await response.json();
                    output.textContent = 'Status: ' + response.status + '\\n\\n' +
                                         JSON.stringify(data, null, 2);
                }} catch (err) {{
                    output.textContent = 'Error: ' + err.message;
                }}
            }}
        </script>
        """

    def _render_calculator(self, config: DemoConfig) -> str:
        """Render an interactive calculator demo."""
        formula = config.data.get("formula", "a + b")
        variables = config.data.get("variables", [{"name": "a", "label": "A", "default": 0}])

        inputs_html = ""
        js_vars = []
        for var in variables:
            name = var.get("name", "")
            label = html.escape(var.get("label", name))
            default = var.get("default", 0)
            min_val = var.get("min", "")
            max_val = var.get("max", "")
            step = var.get("step", "any")

            inputs_html += f"""
            <div style="margin-bottom: 0.5em;">
                <label style="font-weight: 600;">{label}</label>
                <input type="number" id="var-{config.id}-{name}" class="demo-input"
                       value="{default}" min="{min_val}" max="{max_val}" step="{step}"
                       oninput="calculate_{config.id}()" style="width: 100px;">
            </div>
            """
            js_vars.append(
                f'const {name} = parseFloat(document.getElementById("var-{config.id}-{name}").value) || 0;'
            )

        return f"""
        {self._base_styles(config)}
        <div class="demo-container-{config.id}">
            <div class="demo-header-{config.id}">{html.escape(config.title)}</div>
            <div class="demo-body-{config.id}">
                <div style="display: flex; gap: 1em; flex-wrap: wrap; align-items: flex-end;">
                    {inputs_html}
                    <div>
                        <label style="font-weight: 600;">Result</label>
                        <div id="result-{config.id}" class="demo-output" style="margin-top: 0; padding: 0.5em 1em;">
                            0
                        </div>
                    </div>
                </div>
                <p style="color: #666; font-size: 0.85em; margin-top: 1em;">
                    Formula: <code>{html.escape(formula)}</code>
                </p>
            </div>
        </div>
        <script>
            function calculate_{config.id}() {{
                try {{
                    {chr(10).join(js_vars)}
                    const result = {formula};
                    document.getElementById('result-{config.id}').textContent =
                        typeof result === 'number' ? result.toFixed(2) : result;
                }} catch (e) {{
                    document.getElementById('result-{config.id}').textContent = 'Error';
                }}
            }}
            calculate_{config.id}();
        </script>
        """

    def _render_timeline(self, config: DemoConfig) -> str:
        """Render an interactive timeline."""
        events = config.data.get("events", [])

        events_html = ""
        for i, event in enumerate(events):
            date = html.escape(event.get("date", ""))
            title = html.escape(event.get("title", ""))
            desc = html.escape(event.get("description", ""))

            events_html += f"""
            <div class="timeline-item" style="{"flex-direction: row-reverse;" if i % 2 else ""}">
                <div class="timeline-content">
                    <div class="timeline-date">{date}</div>
                    <div class="timeline-title">{title}</div>
                    <div class="timeline-desc">{desc}</div>
                </div>
            </div>
            """

        return f"""
        {self._base_styles(config)}
        <style>
            .timeline-{config.id} {{
                position: relative;
                padding: 1em 0;
            }}
            .timeline-{config.id}::before {{
                content: '';
                position: absolute;
                left: 50%;
                top: 0;
                bottom: 0;
                width: 2px;
                background: {self.accent};
            }}
            .timeline-item {{
                display: flex;
                justify-content: flex-start;
                padding: 0.5em 0;
                width: 50%;
            }}
            .timeline-item:nth-child(odd) {{
                margin-left: 50%;
            }}
            .timeline-content {{
                background: #f9f9f9;
                padding: 1em;
                border-radius: 4px;
                border-left: 3px solid {self.accent};
                max-width: 90%;
            }}
            .timeline-date {{
                color: {self.accent};
                font-weight: 600;
                font-size: 0.85em;
            }}
            .timeline-title {{
                font-weight: 600;
                margin: 0.25em 0;
            }}
            .timeline-desc {{
                font-size: 0.9em;
                color: #666;
            }}
        </style>
        <div class="demo-container-{config.id}">
            <div class="demo-header-{config.id}">{html.escape(config.title)}</div>
            <div class="demo-body-{config.id}">
                <div class="timeline-{config.id}">
                    {events_html}
                </div>
            </div>
        </div>
        """

    def _render_comparison(self, config: DemoConfig) -> str:
        """Render a side-by-side comparison."""
        items = config.data.get("items", [])
        features = config.data.get("features", [])

        header_html = "<tr><th>Feature</th>"
        for item in items:
            header_html += f"<th>{html.escape(item.get('name', ''))}</th>"
        header_html += "</tr>"

        rows_html = ""
        for feature in features:
            rows_html += f"<tr><td><strong>{html.escape(feature.get('name', ''))}</strong></td>"
            for item in items:
                value = item.get("features", {}).get(feature.get("id", ""), "")
                if isinstance(value, bool):
                    cell = "✓" if value else "✗"
                    color = "green" if value else "red"
                    rows_html += f'<td style="color: {color}; text-align: center;">{cell}</td>'
                else:
                    rows_html += f"<td>{html.escape(str(value))}</td>"
            rows_html += "</tr>"

        return f"""
        {self._base_styles(config)}
        <div class="demo-container-{config.id}">
            <div class="demo-header-{config.id}">{html.escape(config.title)}</div>
            <div class="demo-body-{config.id}">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead style="background: {self.primary}; color: white;">
                        {header_html}
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
        <style>
            .demo-container-{config.id} table td,
            .demo-container-{config.id} table th {{
                padding: 0.75em;
                border: 1px solid #ddd;
            }}
            .demo-container-{config.id} table tr:nth-child(even) {{
                background: #f9f9f9;
            }}
        </style>
        """

    def _render_quiz(self, config: DemoConfig) -> str:
        """Render an interactive quiz."""
        questions = config.data.get("questions", [])

        questions_html = ""
        for i, q in enumerate(questions):
            text = html.escape(q.get("question", ""))
            options = q.get("options", [])
            correct = q.get("correct", 0)

            options_html = ""
            for j, opt in enumerate(options):
                options_html += f"""
                <label style="display: block; margin: 0.25em 0; cursor: pointer;">
                    <input type="radio" name="q{i}-{config.id}" value="{j}" data-correct="{correct}">
                    {html.escape(opt)}
                </label>
                """

            questions_html += f"""
            <div class="quiz-question" data-index="{i}">
                <p style="font-weight: 600;">{i + 1}. {text}</p>
                {options_html}
            </div>
            """

        return f"""
        {self._base_styles(config)}
        <div class="demo-container-{config.id}">
            <div class="demo-header-{config.id}">{html.escape(config.title)}</div>
            <div class="demo-body-{config.id}">
                <form id="quiz-{config.id}">
                    {questions_html}
                    <button type="button" class="demo-btn" onclick="checkQuiz_{config.id}()">
                        Check Answers
                    </button>
                </form>
                <div id="quiz-result-{config.id}" class="demo-output" style="display: none;"></div>
            </div>
        </div>
        <script>
            function checkQuiz_{config.id}() {{
                const form = document.getElementById('quiz-{config.id}');
                const questions = form.querySelectorAll('.quiz-question');
                let correct = 0;

                questions.forEach((q, i) => {{
                    const selected = q.querySelector('input:checked');
                    if (selected) {{
                        const correctAns = parseInt(selected.dataset.correct);
                        if (parseInt(selected.value) === correctAns) {{
                            correct++;
                            q.style.borderLeft = '3px solid green';
                        }} else {{
                            q.style.borderLeft = '3px solid red';
                        }}
                    }}
                }});

                const result = document.getElementById('quiz-result-{config.id}');
                result.style.display = 'block';
                result.textContent = 'Score: ' + correct + ' / ' + questions.length;
            }}
        </script>
        """

    def _render_generic(self, config: DemoConfig) -> str:
        """Render a generic demo container."""
        content = html.escape(json.dumps(config.data, indent=2))

        return f"""
        {self._base_styles(config)}
        <div class="demo-container-{config.id}">
            <div class="demo-header-{config.id}">{html.escape(config.title)}</div>
            <div class="demo-body-{config.id}">
                <pre class="demo-output">{content}</pre>
            </div>
        </div>
        """


class DemoLoader:
    """Loads demo configurations from YAML files."""

    def __init__(self, project):
        self.project = project

    def load(self, demo_path: Path) -> DemoConfig:
        """Load a demo from YAML file."""
        import yaml

        with open(demo_path) as f:
            data = yaml.safe_load(f)

        return DemoConfig(
            id=data.get("id", demo_path.stem),
            type=DemoType(data.get("type", "code_playground")),
            title=data.get("title", demo_path.stem),
            description=data.get("description", ""),
            width=data.get("width", "100%"),
            height=data.get("height", "400px"),
            theme=data.get("theme", "light"),
            editable=data.get("editable", True),
            autorun=data.get("autorun", True),
            data=data.get("data", {}),
        )

    def list_demos(self, language: str = None) -> list[Path]:
        """List all demo files."""
        demos = []
        base = self.project.content_dir

        if language:
            demo_dir = base / language / "demos"
            if demo_dir.exists():
                demos.extend(demo_dir.glob("*.yaml"))
        else:
            for lang in self.project.languages:
                demo_dir = base / lang / "demos"
                if demo_dir.exists():
                    demos.extend(demo_dir.glob("*.yaml"))

        return sorted(demos)


class DemoBuilder:
    """
    Builds interactive demos for inclusion in documentation.

    Usage:
        builder = DemoBuilder(project)
        html = builder.build_demo(demo_path)
        builder.build_all_demos(output_dir)
    """

    def __init__(self, project):
        self.project = project
        self.loader = DemoLoader(project)
        self.renderer = DemoRenderer(theme=project.theme if hasattr(project, "theme") else None)

    def build_demo(self, demo_path: Path) -> str:
        """Build a single demo to HTML."""
        config = self.loader.load(demo_path)
        return self.renderer.render(config)

    def build_all_demos(self, output_dir: Path = None) -> list[Path]:
        """Build all demos to HTML files."""
        output_dir = output_dir or self.project.output_dir / "demos"
        output_dir.mkdir(parents=True, exist_ok=True)
        generated = []

        for demo_path in self.loader.list_demos():
            config = self.loader.load(demo_path)
            html_content = self._wrap_standalone(config, self.renderer.render(config))

            # Determine output path
            rel = demo_path.relative_to(self.project.content_dir)
            out_path = output_dir / rel.with_suffix(".html")
            out_path.parent.mkdir(parents=True, exist_ok=True)

            out_path.write_text(html_content)
            generated.append(out_path)

        return generated

    def _wrap_standalone(self, config: DemoConfig, demo_html: str) -> str:
        """Wrap demo in standalone HTML document."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(config.title)}</title>
</head>
<body style="margin: 2em; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <h1>{html.escape(config.title)}</h1>
    <p>{html.escape(config.description)}</p>
    {demo_html}
</body>
</html>
"""


def build_demos(project, output_dir: Path = None) -> list[Path]:
    """Convenience function to build all project demos."""
    builder = DemoBuilder(project)
    return builder.build_all_demos(output_dir)


__all__ = [
    "DemoType",
    "DemoConfig",
    "DemoRenderer",
    "DemoLoader",
    "DemoBuilder",
    "build_demos",
]
