#!/usr/bin/env python3
"""
A simple command-line calculator with basic arithmetic operations.
Supports addition, subtraction, multiplication, and division.
"""


def add(a, b):
    """Add two numbers and return the result."""
    return a + b


def subtract(a, b):
    """Subtract b from a and return the result."""
    return a - b


def multiply(a, b):
    """Multiply two numbers and return the result."""
    return a * b


def divide(a, b):
    """Divide a by b and return the result."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def get_numeric_input(prompt):
    """
    Get numeric input from the user.
    Keeps asking until valid numeric input is provided.
    """
    while True:
        try:
            value = float(input(prompt))
            return value
        except ValueError:
            print("Invalid input. Please enter a numeric value.")


def get_operation():
    """
    Get the operation choice from the user.
    Keeps asking until a valid operation is provided.
    """
    valid_operations = {
        "+": "addition",
        "-": "subtraction",
        "*": "multiplication",
        "/": "division"
    }
    
    while True:
        operation = input("Enter the operation (+, -, *, /): ")
        if operation in valid_operations:
            return operation
        print(f"Invalid operation. Please choose from: {', '.join(valid_operations.keys())}")


def calculate(a, operation, b):
    """
    Perform the calculation based on the operation.
    Returns the result of the calculation.
    """
    operations = {
        "+": add,
        "-": subtract,
        "*": multiply,
        "/": divide
    }
    
    try:
        result = operations[operation](a, b)
        return result
    except ValueError as e:
        print(f"Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def display_result(a, operation, b, result):
    """Display the calculation and its result."""
    if result is not None:
        print(f"\nCalculation: {a} {operation} {b} = {result}")


def calculator_interface():
    """Main calculator interface function."""
    print("=== Simple Command-Line Calculator ===")
    print("You can perform basic arithmetic operations: +, -, *, /")
    print("Type 'q' at any prompt to quit\n")
    
    while True:
        # Get first number
        first_input = input("Enter the first number (or 'q' to quit): ")
        if first_input.lower() == 'q':
            break
        
        try:
            first_number = float(first_input)
        except ValueError:
            print("Invalid input. Please enter a numeric value.")
            continue
        
        # Get operation
        operation_input = input("Enter the operation (+, -, *, /) or 'q' to quit: ")
        if operation_input.lower() == 'q':
            break
        
        if operation_input not in ['+', '-', '*', '/']:
            print("Invalid operation. Please choose from: +, -, *, /")
            continue
        
        # Get second number
        second_input = input("Enter the second number (or 'q' to quit): ")
        if second_input.lower() == 'q':
            break
        
        try:
            second_number = float(second_input)
        except ValueError:
            print("Invalid input. Please enter a numeric value.")
            continue
        
        # Perform calculation
        result = calculate(first_number, operation_input, second_number)
        display_result(first_number, operation_input, second_number, result)
        print("\n-----------------------------------\n")


def main():
    """Main function to run the calculator."""
    try:
        calculator_interface()
        print("Thank you for using the calculator. Goodbye!")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user. Exiting calculator.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
