def detect_vowel(filename:str) -> int:
    # list of Thai vowels
    vowels = [
        "ั",
        "ำ",
        "ิ",
        "ี",
        "ึ",
        "ื",
        "ุ",
        "ู",
        "ฺ",
        "็",
        "่",
        "้",
        "๊", ]
    
    with open(filename, "r", encoding="utf-8") as f:
        count = 0
        for line in f:
            for vowel in vowels:
                count += line.count(vowel)

    return count

if __name__ == "__main__":
    script = input("File Name: ")
    print(detect_vowel(script))