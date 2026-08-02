import sys

def main():
    filepath = r"c:\Users\mahdi\Desktop\CodProj\CtrlRelay\main.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    definition_count = 0
    i = 0
    new_lines = []
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("def setup_handlers"):
            definition_count += 1
            if definition_count == 3:
                # Check the next 6 lines for the expected pattern (stripped)
                if i + 6 < len(lines):
                    lines_to_check = [lines[i+j].strip() for j in range(1, 7)]
                    expected = [
                        '"""Set up all command handlers for the bot."""',
                        'for _, module_name, _ in pkgutil.walk_packages(handlers.__path__, prefix="handlers."):',
                        'module = importlib.import_module(module_name)',
                        'if hasattr(module, "setup") and callable(module.setup):',
                        'logger.info(f"Running {module_name}.setup()")',
                        'module.setup(app)'
                    ]
                    if lines_to_check == expected:
                        # Skip these 7 lines
                        i += 7
                        continue
        # If we are not skipping, add the line
        new_lines.append(line)
        i += 1

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    main()