def cause_an_error():
    print("--- Starting the test ---")
    some_variable = None
    # Эта строка гарантированно вызовет ошибку
    print(some_variable.this_will_fail)
    print("--- This line should not be reached ---")


if __name__ == "__main__":
    cause_an_error()
