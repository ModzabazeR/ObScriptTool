def detect_vowel(filename: str) -> int:
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
        "๊",
        "๋",
        "์", ]

    vowels_data = {
        "ั": {
            "name": "ไม้หันอากาศ (mai hanakard)",
            "count": 0},
        "ำ": {
            "name": "สระอำ (sara um)",
            "count": 0},
        "ิ": {
            "name": "สระอิ (sara i)",
            "count": 0},
        "ี": {
            "name": "สระอี (sara ii)",
            "count": 0},
        "ึ": {
            "name": "สระอึ (sara ei)",
            "count": 0},
        "ื": {
            "name": "สระอือ (sara eei)",
            "count": 0},
        "ุ": {
            "name": "สระอุ (sara u)",
            "count": 0},
        "ู": {
            "name": "สระอู (sara uu)",
            "count": 0},
        "ฺ": {
            "name": "พินทุ (pintu)",
            "count": 0},
        "็": {
            "name": "ไม้ไต่คู้ (mai taiku)",
            "count": 0},
        "่": {
            "name": "ไม้เอก (mai eak)",
            "count": 0},
        "้": {
            "name": "ไม้โท (mai too)",
            "count": 0},
        "๊": {
            "name": "ไม้ตรี (mai tree)",
            "count": 0},
        "๋": {
            "name": "ไม้จัตวา (mai jattawa)",
            "count": 0},
        "์": {
            "name": "การันต์ (karan)",
            "count": 0},
    }

    with open(filename, "r", encoding="utf-8") as f:
        count = 0
        for line in f:
            for vowel in vowels:
                if vowel in line:
                    vowels_data[vowel]["count"] += 1
                    count += 1

    if count > 0:
        print()
        for vowel in vowels_data:
            if vowels_data[vowel]["count"] > 0:
                print(f"{vowels_data[vowel]['name']} : {vowels_data[vowel]['count']}")
        print()

    return count


if __name__ == "__main__":
    script = input("File Name: ")
    print(detect_vowel(script))
