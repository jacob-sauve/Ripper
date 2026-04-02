#!/usr/bin/env python3

def parse_commandfile(filename, funcdict, debug=False):
    """return list of parsed commands from file filename"""
    with open(filename, "rt") as f:
        lines = f.readlines()
        if debug:
            print(lines)
    commands = list()
    for commandstring in lines:
        command, *args = commandstring.rstrip('\n').split(' ')
        check = len(args) == len(list(filter(lambda x: x.lstrip('-').isdecimal(), args)))
        if (not command.upper() in funcdict) or (not check):
            if debug:
                print(f"Invalid command: '{command}'")
        else:
            if debug:
                print(f"Executing command: {command}")
            commands.append((command.upper(), *list(map(int, args))))
    if debug:
        print("commands:", *commands, sep="\n")
    return commands



if __name__ == "__main__":
    try:
        from time import sleep
        import titlecard
        from multi_process_drive import Megamind
        brain = Megamind({})
        titlecard.show()
        commands = parse_commandfile("commands.txt", brain.funcdict, debug=True)
    except BaseException as e:
        print(e)
    finally:
        print("testing complete")
