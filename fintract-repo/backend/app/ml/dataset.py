"""Labeled training corpus for the expense-categorization model.

Kept in code so the model is reproducible and trainable offline with no external
downloads. Expand this list to improve accuracy / support retraining.
"""

TRAINING_DATA: list[tuple[str, str]] = [
    # Food
    ("swiggy dinner order", "Food"), ("zomato lunch", "Food"),
    ("bigbasket groceries", "Food"), ("restaurant bill", "Food"),
    ("dominos pizza", "Food"), ("cafe coffee day", "Food"),
    ("starbucks latte", "Food"), ("grocery store milk eggs", "Food"),
    ("mcdonalds burger", "Food"), ("dinner with friends", "Food"),
    ("kfc chicken bucket", "Food"), ("blinkit vegetables", "Food"),
    ("uber eats meal", "Food"), ("bakery bread", "Food"),
    ("food court lunch", "Food"), ("street food snacks", "Food"),
    # Travel
    ("uber to airport", "Travel"), ("ola cab ride", "Travel"),
    ("petrol pump fuel", "Travel"), ("indigo flight ticket", "Travel"),
    ("irctc train booking", "Travel"), ("metro card recharge", "Travel"),
    ("rapido bike ride", "Travel"), ("bus ticket", "Travel"),
    ("toll gate payment", "Travel"), ("car parking fee", "Travel"),
    ("hp petrol", "Travel"), ("flight to delhi", "Travel"),
    ("taxi fare", "Travel"), ("diesel refill", "Travel"),
    ("makemytrip hotel", "Travel"), ("airbnb stay", "Travel"),
    # Shopping
    ("amazon headphones", "Shopping"), ("myntra apparel", "Shopping"),
    ("flipkart mobile case", "Shopping"), ("nike shoes", "Shopping"),
    ("zara t-shirt", "Shopping"), ("shopping mall clothes", "Shopping"),
    ("ajio dress", "Shopping"), ("ikea furniture", "Shopping"),
    ("decathlon sports gear", "Shopping"), ("watch purchase", "Shopping"),
    ("sunglasses ray ban", "Shopping"), ("new laptop bag", "Shopping"),
    # Bills
    ("electricity bill", "Bills"), ("water bill payment", "Bills"),
    ("mobile recharge airtel", "Bills"), ("broadband internet bill", "Bills"),
    ("gas cylinder booking", "Bills"), ("house rent", "Bills"),
    ("dth recharge", "Bills"), ("maintenance charges", "Bills"),
    ("postpaid bill jio", "Bills"), ("credit card bill", "Bills"),
    ("insurance premium", "Bills"), ("wifi bill", "Bills"),
    # Healthcare
    ("apollo pharmacy medicine", "Healthcare"), ("hospital consultation", "Healthcare"),
    ("doctor visit fee", "Healthcare"), ("dental checkup", "Healthcare"),
    ("blood test lab", "Healthcare"), ("pharmeasy medicines", "Healthcare"),
    ("eye clinic", "Healthcare"), ("physiotherapy session", "Healthcare"),
    ("vaccination", "Healthcare"), ("health supplements", "Healthcare"),
    # Entertainment
    ("netflix subscription", "Entertainment"), ("spotify premium", "Entertainment"),
    ("movie tickets bookmyshow", "Entertainment"), ("amazon prime video", "Entertainment"),
    ("playstation game", "Entertainment"), ("concert ticket", "Entertainment"),
    ("hotstar subscription", "Entertainment"), ("bowling with friends", "Entertainment"),
    ("theme park entry", "Entertainment"), ("youtube premium", "Entertainment"),
    # Education
    ("coursera course fee", "Education"), ("udemy python course", "Education"),
    ("college tuition fee", "Education"), ("textbook purchase", "Education"),
    ("online workshop", "Education"), ("school fees", "Education"),
    ("exam registration", "Education"), ("kindle ebook", "Education"),
    ("coaching classes", "Education"), ("certification exam", "Education"),
    # Investments
    ("sip nifty index fund", "Investments"), ("mutual fund purchase", "Investments"),
    ("stock market zerodha", "Investments"), ("etf investment", "Investments"),
    ("gold bond purchase", "Investments"), ("fixed deposit", "Investments"),
    ("ppf contribution", "Investments"), ("crypto bitcoin", "Investments"),
    ("recurring deposit", "Investments"), ("nps retirement", "Investments"),
    # Others
    ("gift for friend", "Others"), ("donation charity", "Others"),
    ("atm cash withdrawal", "Others"), ("miscellaneous expense", "Others"),
    ("temple offering", "Others"), ("pet supplies", "Others"),
    ("home repair", "Others"), ("stationery items", "Others"),
    ("salon haircut", "Others"), ("laundry service", "Others"),
]
