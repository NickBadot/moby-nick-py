

def count_substring_in_matrix (matrix, substring):
    output = []  # we want to return a list of counts so initialise an empty list
    for line in matrix:  # iterate through the first list, note the matrix is a list of lists so "line" here is a list
        line = "".join(line)  # convert the current line of the matrix into str by joining to empty string
        output.append(line.count(substring))  # for each line we want to calculate the count and add it to our empty list
    return output


def count_substring_in_matrix_but_in_one_line_just_to_show_off (matrix, substring):
    return ["".join(line).count(substring) for line in matrix] # I love list comprehensions,
    # maybe don't submit this one but it would be good to try and understand it


def main():
    input_matrix = [["a", "b", "b", "a"], ["a", "c", "c", "a"], ["b", "a", "b", "a" ], ["a", "b", "a", "f"]]
    substring = "ba"
    print(count_substring_in_matrix(input_matrix, substring))
    print(count_substring_in_matrix_but_in_one_line_just_to_show_off(input_matrix, substring))


if __name__ == "__main__":
    main()
