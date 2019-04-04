class Account:
    def __init__(self, balance=0):
        self.balance = balance
        self.rental_profits = 0

    def add(self, amount):
        self.balance += amount

    def subtract(self, amount):
        self.balance -= amount

    def rental(self, price):
        self.rental_profits += price
