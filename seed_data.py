import json
from extensions import db
from models import Question


# Each tuple:
# (text, [4 options], correct_index, ai_correct_bool)
#
# ai_correct currently represents the AI benchmark.
# We will change this later to a genuinely live AI-generated score.


# ============================================================
# BEGINNER — 15 QUESTIONS
# ============================================================

BEGINNER = [

    ("What comes next: 2, 4, 6, 8, ?",
     ["9", "10", "11", "12"], 1, True),

    ("Which word means the opposite of 'hot'?",
     ["Warm", "Cold", "Wet", "Fast"], 1, True),

    ("How many days are there in a week?",
     ["5", "6", "7", "8"], 2, True),

    ("Which one is a fruit?",
     ["Carrot", "Apple", "Potato", "Onion"], 1, True),

    ("What is 5 + 3?",
     ["7", "8", "9", "6"], 1, True),

    ("Which animal says 'moo'?",
     ["Dog", "Cat", "Cow", "Duck"], 2, True),

    ("Which shape has 3 sides?",
     ["Square", "Circle", "Triangle", "Rectangle"], 2, True),

    ("What color do you get by mixing blue and yellow?",
     ["Purple", "Green", "Orange", "Pink"], 1, True),

    ("Which is the largest number?",
     ["45", "54", "27", "39"], 1, True),

    ("What do you use to write on paper?",
     ["Spoon", "Pen", "Plate", "Shoe"], 1, True),

    ("Which one is a season?",
     ["Monday", "Winter", "Red", "Circle"], 1, True),

    ("What is the first letter of the alphabet?",
     ["B", "Z", "A", "M"], 2, True),

    ("Which of these is a vehicle?",
     ["Chair", "Car", "Table", "Lamp"], 1, True),

    ("How many legs does a spider have?",
     ["6", "8", "4", "10"], 1, False),

    ("What comes next: Monday, Tuesday, ?",
     ["Thursday", "Sunday", "Wednesday", "Friday"], 2, True),
]


# ============================================================
# INTERMEDIATE — ORIGINAL 30 QUESTIONS
# ============================================================

INTERMEDIATE = [

    ("What does CPU stand for?",
     ["Central Processing Unit",
      "Computer Personal Unit",
      "Central Program Utility",
      "Control Processing Unit"], 0, True),

    ("Which language is primarily used for styling web pages?",
     ["HTML", "CSS", "Python", "SQL"], 1, True),

    ("What does HTML stand for?",
     ["Hyper Trainer Markup Language",
      "HyperText Markup Language",
      "HyperText Markdown Language",
      "Hyper Tool Multi Language"], 1, True),

    ("Which of these is a version control system?",
     ["Git", "Excel", "Photoshop", "Slack"], 0, True),

    ("What is the binary equivalent of decimal 2?",
     ["01", "10", "11", "00"], 1, True),

    ("Which symbol is used for comments in Python?",
     ["//", "#", "<!-- -->", "**"], 1, True),

    ("What does SQL stand for?",
     ["Structured Query Language",
      "Simple Question Language",
      "Structured Question Logic",
      "System Query Language"], 0, True),

    ("Which company developed the Python language?",
     ["Google", "Microsoft", "None (open community)", "Apple"], 2, False),

    ("What data type is used to store True/False in most languages?",
     ["Integer", "Boolean", "String", "Float"], 1, True),

    ("What does RAM stand for?",
     ["Random Access Memory",
      "Read Access Memory",
      "Run Active Memory",
      "Random Active Module"], 0, True),

    ("Which HTTP method is typically used to fetch data?",
     ["POST", "GET", "DELETE", "PUT"], 1, True),

    ("Which of these is NOT a programming language?",
     ["Java", "Python", "HTML", "C++"], 2, True),

    ("What is the file extension for Python files?",
     [".py", ".pt", ".pyt", ".pi"], 0, True),

    ("Which symbol represents 'not equal to' in Python?",
     ["<>", "!=", "=/=", "~="], 1, True),

    ("What does IDE stand for?",
     ["Integrated Development Environment",
      "Internal Data Engine",
      "Interactive Design Editor",
      "Integrated Design Element"], 0, True),

    ("What is the output of 5 % 2 in most languages?",
     ["2", "1", "0", "2.5"], 1, True),

    ("Which of these stores data in rows and columns?",
     ["Database table", "Function", "Loop", "Variable"], 0, True),

    ("Which company created the Java language?",
     ["Sun Microsystems", "Microsoft", "IBM", "Google"], 0, False),

    ("What does API stand for?",
     ["Application Programming Interface",
      "Applied Program Instruction",
      "Automated Programming Interface",
      "Application Process Integration"], 0, True),

    ("Which of the following is a NoSQL database?",
     ["MongoDB", "MySQL", "PostgreSQL", "SQLite"], 0, True),

    ("What is the correct file extension for JavaScript files?",
     [".js", ".java", ".jsx", ".javascript"], 0, True),

    ("Which loop runs at least once even if the condition is false?",
     ["for", "while", "do-while", "foreach"], 2, True),

    ("What does 'CSS' stand for?",
     ["Cascading Style Sheets",
      "Computer Style System",
      "Creative Style Sheets",
      "Cascading System Style"], 0, True),

    ("Which keyword is used to define a function in Python?",
     ["func", "def", "function", "define"], 1, True),

    ("Which port does HTTP use by default?",
     ["21", "80", "443", "8080"], 1, True),

    ("What does URL stand for?",
     ["Uniform Resource Locator",
      "Universal Reference Link",
      "Uniform Reference Locator",
      "Universal Resource Link"], 0, True),

    ("Which of these is a cloud service provider?",
     ["AWS", "Photoshop", "Excel", "Notepad"], 0, True),

    ("What is the primary key used for in a database table?",
     ["Uniquely identify a row",
      "Sort columns",
      "Encrypt data",
      "Delete rows"], 0, True),

    ("Which of these is a valid Python list?",
     ["(1,2,3)", "[1,2,3]", "{1,2,3}", "<1,2,3>"], 1, True),

    ("What does 'git commit' do?",
     ["Saves a snapshot of changes",
      "Deletes a branch",
      "Uploads to server",
      "Creates a repository"], 0, True),
]


# ============================================================
# INTERMEDIATE — 15 NEW LOGIC / MATH / REASONING QUESTIONS
# ============================================================

INTERMEDIATE_EXTRA = [

    ("What comes next: 3, 6, 12, 24, ?",
     ["36", "42", "48", "54"], 2, True),

    ("A number is increased by 20% and then decreased by 20%. What is the overall change?",
     ["No change", "4% decrease", "4% increase", "2% decrease"], 1, True),

    ("A train travels 60 km in 1.5 hours. What is its average speed?",
     ["30 km/h", "40 km/h", "45 km/h", "60 km/h"], 1, True),

    ("What comes next: 2, 5, 11, 23, ?",
     ["35", "41", "47", "49"], 2, True),

    ("A fair coin is tossed once. What is the probability of getting heads?",
     ["1/4", "1/2", "2/3", "1"], 1, True),

    ("A basket contains 10 red balls and 10 blue balls. What is the minimum number of balls you must pick to guarantee two of the same color?",
     ["2", "3", "4", "5"], 1, True),

    ("Which number does not belong to the group?",
     ["8", "27", "64", "100"], 3, True),

    ("If 5 machines make 5 products in 5 minutes, how long would 100 machines take to make 100 products?",
     ["5 minutes", "20 minutes", "100 minutes", "500 minutes"], 0, True),

    ("What is the next number: 1, 4, 9, 16, 25, ?",
     ["30", "36", "40", "49"], 1, True),

    ("A father is 30 years older than his son. In 5 years, the father will be twice the son's age. How old is the son now?",
     ["20", "25", "30", "35"], 1, True),

    ("If TODAY is coded by shifting every letter one position forward in the alphabet, how is TODAY coded?",
     ["UPBDB", "UPEBZ", "TPEBZ", "VQFCB"], 1, True),

    ("A clock shows exactly 3:00. What is the angle between the hour and minute hands?",
     ["0°", "30°", "90°", "180°"], 2, True),

    ("A car travels 120 km in 2 hours. At the same speed, how far will it travel in 5 hours?",
     ["240 km", "300 km", "360 km", "400 km"], 1, True),

    ("What comes next: Monday, Wednesday, Friday, ?",
     ["Saturday", "Sunday", "Tuesday", "Thursday"], 1, True),

    ("You have 3 boxes labeled Apples, Oranges and Mixed. Every label is wrong. What is the minimum number of fruits you need to pick to correctly identify all three boxes?",
     ["1", "2", "3", "4"], 0, True),
]


# ============================================================
# ADVANCED — ORIGINAL 30 QUESTIONS
# ============================================================

ADVANCED = [

    ("What is the time complexity of binary search?",
     ["O(n)", "O(log n)", "O(n^2)", "O(1)"], 1, True),

    ("Which data structure uses LIFO order?",
     ["Queue", "Stack", "Array", "Linked List"], 1, True),

    ("What does ACID stand for in databases?",
     ["Atomicity, Consistency, Isolation, Durability",
      "Access, Control, Integrity, Data",
      "Atomic, Concurrent, Isolated, Durable",
      "Accuracy, Consistency, Integrity, Durability"], 0, True),

    ("Which sorting algorithm has the best average time complexity?",
     ["Bubble Sort", "Quick Sort", "Selection Sort", "Insertion Sort"], 1, True),

    ("What is the purpose of a foreign key?",
     ["Link two tables together",
      "Encrypt data",
      "Speed up deletes",
      "Store passwords"], 0, True),

    ("In REST APIs, which status code means 'Not Found'?",
     ["200", "301", "404", "500"], 2, True),

    ("Which HTTP status code indicates successful creation of a resource?",
     ["200", "201", "204", "202"], 1, True),

    ("What does JWT stand for?",
     ["JSON Web Token",
      "Java Web Tool",
      "JavaScript Web Token",
      "JSON Web Type"], 0, True),

    ("What is the primary purpose of indexing in a database?",
     ["Speed up read queries",
      "Reduce storage",
      "Encrypt data",
      "Backup data"], 0, True),

    ("Which design pattern restricts a class to a single instance?",
     ["Factory", "Singleton", "Observer", "Builder"], 1, True),

    ("What does CORS stand for?",
     ["Cross-Origin Resource Sharing",
      "Central Origin Request System",
      "Cross-Origin Request Standard",
      "Client Origin Resource Sharing"], 0, False),

    ("Which of these is used for container orchestration?",
     ["Docker Compose", "Kubernetes", "Git", "Nginx"], 1, True),

    ("What is a race condition?",
     ["Two processes competing for the same resource unpredictably",
      "A network speed test",
      "A CPU scheduling algorithm",
      "A type of deadlock"], 0, True),

    ("Which HTTP method is idempotent?",
     ["POST", "PUT", "PATCH", "CONNECT"], 1, True),

    ("What does ORM stand for?",
     ["Object Relational Mapping",
      "Online Resource Manager",
      "Object Runtime Module",
      "Ordered Resource Mapping"], 0, True),

    ("In Big-O notation, what is the complexity of accessing an array element by index?",
     ["O(1)", "O(n)", "O(log n)", "O(n log n)"], 0, True),

    ("Which of these is NOT a valid HTTP method?",
     ["GET", "POST", "FETCH", "DELETE"], 2, True),

    ("What is the purpose of a webhook?",
     ["Push real-time event notifications to another server",
      "Cache static files",
      "Compress images",
      "Encrypt passwords"], 0, True),

    ("Which consistency model does most SQL databases follow by default?",
     ["Eventual consistency",
      "Strong consistency",
      "Causal consistency",
      "Weak consistency"], 1, False),

    ("What does the acronym 'CI/CD' stand for?",
     ["Continuous Integration / Continuous Deployment",
      "Code Inspection / Code Delivery",
      "Continuous Inspection / Continuous Delivery",
      "Code Integration / Continuous Development"], 0, True),

    ("Which algorithmic technique does merge sort use?",
     ["Divide and conquer",
      "Greedy",
      "Dynamic programming",
      "Backtracking"], 0, True),

    ("What is a deadlock?",
     ["Two or more processes waiting on each other indefinitely",
      "A crashed server",
      "A failed API call",
      "A memory leak"], 0, True),

    ("What does the 'S' in HTTPS stand for?",
     ["Secure", "Server", "Session", "System"], 0, True),

    ("Which of these best describes a microservices architecture?",
     ["Small independent services communicating over a network",
      "One large monolithic application",
      "A single database shared by all modules",
      "A frontend-only architecture"], 0, True),

    ("What is normalization in database design primarily used for?",
     ["Reducing data redundancy",
      "Increasing storage size",
      "Speeding up writes only",
      "Encrypting tables"], 0, True),

    ("Which caching strategy stores data closest to the user?",
     ["CDN caching",
      "Database caching",
      "Server-side caching",
      "Disk caching"], 0, True),

    ("What is the main advantage of using an index in SQL?",
     ["Faster SELECT queries",
      "Faster INSERT queries always",
      "Smaller database size",
      "Better security"], 0, True),

    ("Which of these is a NoSQL document database?",
     ["MongoDB", "PostgreSQL", "MySQL", "Oracle DB"], 0, True),

    ("What does 'idempotent' mean in the context of APIs?",
     ["Repeating the request has the same effect as calling it once",
      "The request always fails",
      "The request modifies multiple resources",
      "The request requires authentication"], 0, True),

    ("Which of these best prevents SQL injection?",
     ["Parameterized queries",
      "Minifying JavaScript",
      "Using GET instead of POST",
      "Increasing server RAM"], 0, True),
]


# ============================================================
# ADVANCED — 15 NEW LOGIC / MATH / REASONING QUESTIONS
# ============================================================

ADVANCED_EXTRA = [

    ("What comes next: 1, 2, 6, 24, 120, ?",
     ["240", "360", "600", "720"], 3, True),

    ("Find the missing number: 1, 4, 10, 22, 46, ?",
     ["82", "90", "94", "96"], 2, True),

    ("A fair die is rolled twice. What is the probability that the sum is 7?",
     ["1/12", "1/9", "1/6", "1/3"], 2, True),

    ("There are 8 people in a room. Everyone shakes hands with everyone else exactly once. How many handshakes occur?",
     ["28", "32", "56", "64"], 0, True),

    ("If x + 1/x = 5, what is x² + 1/x²?",
     ["23", "24", "25", "27"], 0, True),

    ("A bag contains 4 red and 6 blue balls. Two balls are drawn without replacement. What is the probability that both are red?",
     ["1/5", "2/15", "4/25", "1/3"], 1, True),

    ("Three workers complete a task in 12 days. Assuming equal productivity, how many days would 9 workers need?",
     ["3", "4", "6", "9"], 1, True),

    ("A man walks 3 km north and then 4 km east. What is his straight-line distance from the starting point?",
     ["3 km", "4 km", "5 km", "7 km"], 2, True),

    ("What comes next: 2, 3, 5, 9, 17, ?",
     ["25", "31", "33", "35"], 2, True),

    ("A system has 99% availability. Approximately what percentage of time is unavailable?",
     ["0.1%", "1%", "9%", "99%"], 1, True),

    ("A fair coin is tossed three times. What is the probability of getting exactly two heads?",
     ["1/8", "2/8", "3/8", "4/8"], 2, True),

    ("Five people sit in a row. A must sit immediately before B. How many arrangements are possible?",
     ["24", "48", "60", "120"], 1, True),

    ("A problem has two independent stages. The first succeeds with probability 0.8 and the second with probability 0.5. What is the probability that both succeed?",
     ["0.3", "0.4", "0.5", "0.8"], 1, True),

    ("Which data structure is generally most appropriate for implementing a priority queue efficiently?",
     ["Stack", "Heap", "Array only", "Linked list only"], 1, True),

    ("A sequence follows the rule: 5, 11, 23, 47, 95, ?. What comes next?",
     ["181", "189", "191", "195"], 2, True),
]


# ============================================================
# SEED QUESTIONS
# ============================================================

def seed_questions():

    # Combine all existing and new questions
    all_questions = []

    # Beginner
    all_questions.extend([
        ("beginner", item)
        for item in BEGINNER
    ])

    # Existing Intermediate
    all_questions.extend([
        ("intermediate", item)
        for item in INTERMEDIATE
    ])

    # New Intermediate
    all_questions.extend([
        ("intermediate", item)
        for item in INTERMEDIATE_EXTRA
    ])

    # Existing Advanced
    all_questions.extend([
        ("advanced", item)
        for item in ADVANCED
    ])

    # New Advanced
    all_questions.extend([
        ("advanced", item)
        for item in ADVANCED_EXTRA
    ])


    # Get question text already present in database
    existing_questions = {
        q.text
        for q in Question.query.all()
    }


    added = 0


    for category, item in all_questions:

        text, options, correct, ai_ok = item


        # Prevent duplicate questions
        if text in existing_questions:
            continue


        db.session.add(
            Question(
                category=category,
                text=text,
                options_json=json.dumps(options),
                correct_index=correct,
                ai_correct=ai_ok,
            )
        )


        existing_questions.add(text)

        added += 1


    db.session.commit()


    print(f"Added {added} new questions.")