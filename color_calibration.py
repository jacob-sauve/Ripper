import src.colors as colors

with open("color_calibration.txt", "r") as file:
    for line in file:
        color = eval(line.strip())
        colors.classify(color, debugging=True)
