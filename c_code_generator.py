import argparse
import os
import sys
import random

lines_counter = 0


def random_bool():
    return bool(random.getrandbits(1))


def random_lifetime():
    return "*" + (
        f"${chr(ord('a') + random.randint(0, NUM_LIFETIMES - 1))} "
        if random_bool()
        else ""
    )


def random_num_indirections():
    return random.choices([1, 2, 3], weights=[80, 15, 5])[0]


def random_indirections_to_var(num_indirections=-1, can_be_addrof=False):
    num_indirections = (
        num_indirections if num_indirections != -1 else random_num_indirections()
    )
    if can_be_addrof:
        new_num_indirections = random.randint(
            max(num_indirections - 1, 1), MAX_NUM_INDIRECTIONS
        )
    else:
        new_num_indirections = random.randint(num_indirections, MAX_NUM_INDIRECTIONS)
    diff = new_num_indirections - num_indirections
    if len(indirections_to_var[new_num_indirections]) < 1 or diff < -1:
        new_num_indirections = num_indirections
        diff = 0
    return random.choice(indirections_to_var[new_num_indirections]), diff


def create_var(num_indirections, can_be_addrof=False):
    var, indirections = random_indirections_to_var(num_indirections, can_be_addrof)
    if indirections > 0:
        return f"{'*'*indirections}v{var}"
    else:
        return f"{'&'*abs(indirections)}v{var}"


def create_declaration(i, num_indirections=-1):
    var_decl = "int "
    num_indirections = (
        num_indirections if num_indirections != -1 else random_num_indirections()
    )
    for _ in range(num_indirections):
        var_decl += random_lifetime()
    var_decl += f"v{i}"
    if len(indirections_to_var[num_indirections]) > 0 and random.choices(
        [True, False], weights=[VAR_DECL_HAS_INIT, 1 - VAR_DECL_HAS_INIT]
    ):
        var_decl += f" = {create_var(num_indirections, True)}"
    var_decl += ";\n"
    indirections_to_var[num_indirections].append(i)
    var_to_indirection[i] = num_indirections
    return var_decl


def create_var_assign(counter, func_idx):
    num_indirections = random_num_indirections()
    res = f"{create_var(num_indirections)} = "
    if (
        len(func_return_dict[num_indirections]) != 0
        and random.choices(
            [True, False], weights=[ASSIGN_HAS_FUNC_CALL, 1 - ASSIGN_HAS_FUNC_CALL]
        )[0]
    ):
        rhs, _ = create_call_expr(counter, func_idx, num_indirections)
    else:
        rhs = create_var(num_indirections, True) + ";\n"
    return res + rhs, counter + 1


def create_if_else(num_vars, counter, func_idx):
    counter += 2
    has_else = random.choices([True, False], weights=[30, 70])
    if has_else:
        counter += 1
    program = f"if (*{create_var(1)} > *{create_var(1)}) {{\n"
    stmt, counter = create_stmt(num_vars, counter, func_idx)
    program += stmt
    if has_else:
        program += "} else {\n"
        stmt, counter = create_stmt(num_vars, counter, func_idx)
        program += stmt
    program += "}\n"
    return program, counter


def create_while(num_vars, counter, func_idx):
    counter += 2
    program = f"while (*{create_var(1)} > 0) {{\n"
    stmt, counter = create_stmt(num_vars, counter, func_idx)
    program += stmt
    program += "}\n"
    return program, counter


def create_call_expr(counter, func_idx, num_indirections=-1):
    if num_indirections == -1:
        call_function = random.randint(1, func_idx)
    else:
        call_function = random.choice(func_return_dict[num_indirections])
    program = f"fn{call_function}("
    if len(func_args_dict[call_function]) > 0:
        for ind in func_args_dict[call_function]:
            program += create_var(ind, True) + ", "
        program = program[:-2]
    return program + ");\n", counter + 1


def create_stmt(num_vars, counter, func_idx):
    choice = random.randint(0, 100) / 100
    if choice < PERCENTAGE_ASSIGNMENTS:
        return create_var_assign(counter, func_idx)
    elif choice < PERCENTAGE_IF_ELSE:
        return create_if_else(num_vars, counter, func_idx)
    elif choice < PERCENTAGE_WHILE:
        return create_while(num_vars, counter, func_idx)
    else:
        return create_call_expr(counter, func_idx)


def create_stmts(num_stmts, num_vars, func_idx):
    stmt_counter = 0
    program = ""
    while stmt_counter < num_stmts:
        stmt, stmt_counter = create_stmt(num_vars, stmt_counter, func_idx)
        program += stmt
    return program, stmt_counter


def createFunctionHeader(func_idx, return_num_indirections, write_to_vars=False):
    # return value
    func_return_dict[return_num_indirections].append(func_idx)
    program = "int "
    for _ in range(return_num_indirections):
        program += random_lifetime()
    program += f"fn{func_idx}("
    num_params = random.randint(0, 8)
    func_args_dict[func_idx] = []

    for i in range(num_params):
        num_indirections = random_num_indirections()
        program += "int "
        for _ in range(num_indirections):
            program += random_lifetime()
        program += f"v{i}"
        if write_to_vars:
            indirections_to_var[num_indirections].append(i)
            var_to_indirection[i] = num_indirections
        func_args_dict[func_idx].append(num_indirections)
        if i != num_params - 1:
            program += ", "
    program += ")"
    return program, num_params


def createFunctionHeaders(program_size):
    global lines_counter
    lines_left = program_size - lines_counter

    num_func_headers = max(int(PERCENTAGE_FUNC_HEADERS * lines_left), 5)

    program = ""

    for i in range(num_func_headers):
        return_num_indirections = random_num_indirections()
        func_header, _ = createFunctionHeader(i + 1, return_num_indirections)
        program += func_header + ";\n"

    lines_counter += num_func_headers
    return program, num_func_headers


def createFunction(func_idx, program_size):
    global lines_counter

    for i in range(1, 4):
        indirections_to_var[i] = []

    # function header, return, }, \n -> 4 lines
    lines_counter += 4
    lines_left = program_size - lines_counter
    return_num_indirections = random_num_indirections()
    program, num_params = createFunctionHeader(func_idx, return_num_indirections, True)
    program += " {\n"

    num_decls = int(PERCENTAGE_VARS * lines_left)

    num_vars = num_decls + num_params

    for i in range(MAX_NUM_INDIRECTIONS):
        program += create_declaration(num_params + i, i + 1)

    for i in range(num_params + 3, num_vars):
        program += create_declaration(i)

    lines_counter += num_decls

    # num_stmt = random.randint(num_decls - 2, num_decls + 5)
    num_stmt = program_size - lines_counter

    stmts, counter = create_stmts(num_stmt, num_vars, func_idx)
    program += stmts
    lines_counter += counter

    program += f"return {create_var(return_num_indirections, True)};\n"
    program += "}\n"
    return program


# ARGS


def get_int_arg(arg, name):
    try:
        return int(arg)
    except ValueError:
        print(f"Error: --{name} must be an integer.")
        sys.exit(1)


def get_float_arg(arg, name):
    try:
        return float(arg)
    except ValueError:
        print(f"Error: --{name} must be a float.")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a C++ test for the static analyzer of C++ Rust-like lifetime annotations."
    )

    parser.add_argument(
        "-a", "--assigns", action="store_true", help="mode: percentage of assignments"
    )
    parser.add_argument(
        "-v", "--vars", action="store_true", help="mode: percentage of variables"
    )
    parser.add_argument(
        "-f",
        "--func-calls",
        action="store_true",
        help="mode: percentage of function calls",
    )
    parser.add_argument("-d", "--debug", default=False, help="verbose mode")
    parser.add_argument("-n", "--name", default="test", help="name of the test")
    parser.add_argument("-s", "--size", default=100, help="number of lines of the test")
    parser.add_argument(
        "-i",
        "--input-value",
        default=0.10,
        help="percentage of variable declarations, function calls or assignments, depending on the mode",
    )
    parser.add_argument(
        "-ml", "--min-lifetimes", default=3, help="min number of lifetimes"
    )
    parser.add_argument(
        "-Ml", "--max-lifetimes", default=8, help="max number of lifetimes"
    )
    args = parser.parse_args()

    program_size = get_int_arg(args.size, "size")
    if program_size < 100:
        print("Error: --size cannot be less than 100.")
        sys.exit(1)

    global NUM_LIFETIMES
    min_lifetimes = get_int_arg(args.min_lifetimes, "min-lifetimes")
    if min_lifetimes < 1:
        print("Error: --min-lifetimes cannot be 0.")
        sys.exit(1)
    max_lifetimes = get_int_arg(args.max_lifetimes, "max-lifetimes")
    if max_lifetimes < min_lifetimes:
        print("Error: --max-lifetimes cannot be less than --min-lifetimes.")
        sys.exit(1)
    elif max_lifetimes > 26:
        print("Error: --max-lifetimes cannot be greater than 26.")
        sys.exit(1)
    NUM_LIFETIMES = random.randint(min_lifetimes, max_lifetimes)

    global PERCENTAGE_VARS, PERCENTAGE_ASSIGNMENTS, PERCENTAGE_IF_ELSE, PERCENTAGE_WHILE, PERCENTAGE_FUNC_CALLS, PERCENTAGE_FUNC_HEADERS, ASSIGN_HAS_FUNC_CALL, VAR_DECL_HAS_INIT

    modes_set = [args.assigns, args.vars, args.func_calls].count(True)
    PERCENTAGE_VARS = 0.20
    # the sum of the following percentages must be 1
    PERCENTAGE_ASSIGNMENTS = 0.45
    PERCENTAGE_IF_ELSE = 0.10
    PERCENTAGE_WHILE = 0.10
    PERCENTAGE_FUNC_CALLS = 0.35
    ASSIGN_HAS_FUNC_CALL = 0.5
    VAR_DECL_HAS_INIT = 0.3

    if modes_set > 1:
        print(f"Choose only one mode: --assigns, --vars or --func-calls.")
        sys.exit(1)
    elif modes_set == 1:
        percentage_input = get_float_arg(args.input_value, "input-value")
        if args.assigns:
            normalized_assigns = (PERCENTAGE_ASSIGNMENTS * (1 - PERCENTAGE_VARS))
            k = (VAR_DECL_HAS_INIT * PERCENTAGE_VARS) / normalized_assigns
            # find the percentage of percentage_input that goes in PERCENTAGE_VAR_DECLS and in PERCENTAGE_ASSIGNMENTS
            # we want k * PERCENTAGE_ASSIGNMENTS + PERCENTAGE_ASSIGNMENTS = percentage_input

            normalized_vars = PERCENTAGE_VARS / (1 - normalized_assigns)
            normalized_if_elses = (PERCENTAGE_IF_ELSE * (1 - PERCENTAGE_VARS)) / (
                1 - normalized_assigns
            )
            normalized_whiles = (PERCENTAGE_WHILE * (1 - PERCENTAGE_VARS)) / (
                1 - normalized_assigns
            )
            normalized_func_calls = (PERCENTAGE_FUNC_CALLS * (1 - PERCENTAGE_VARS)) / (
                1 - normalized_assigns
            )

            total_assignments = percentage_input / (k + 1)
            PERCENTAGE_VARS = normalized_vars * (1 - total_assignments)
            
            PERCENTAGE_IF_ELSE = (normalized_if_elses * (1 - total_assignments)) / (
                1 - PERCENTAGE_VARS
            )
            PERCENTAGE_WHILE = (normalized_whiles * (1 - total_assignments)) / (
                1 - PERCENTAGE_VARS
            )
            PERCENTAGE_FUNC_CALLS = (
                normalized_func_calls * (1 - total_assignments)
            ) / (1 - PERCENTAGE_VARS)

            var_decls_with_assignments = k * total_assignments
            VAR_DECL_HAS_INIT = var_decls_with_assignments / PERCENTAGE_VARS

            PERCENTAGE_ASSIGNMENTS = total_assignments / (1 - PERCENTAGE_VARS)

            print(
                f"Vars:\t{PERCENTAGE_VARS}\nAssignments:\t{PERCENTAGE_ASSIGNMENTS}\nIfElse:\t{PERCENTAGE_IF_ELSE}\nWhile:\t{PERCENTAGE_WHILE}\nFunction calls:\t{PERCENTAGE_FUNC_CALLS}"
            )
            print(f"Percentage function calls in assignments:\t{VAR_DECL_HAS_INIT}")
            print(
                f"Total:\t{PERCENTAGE_ASSIGNMENTS + PERCENTAGE_IF_ELSE + PERCENTAGE_WHILE + PERCENTAGE_FUNC_CALLS}"
            )
            print(
                f"A_F / F: {(VAR_DECL_HAS_INIT * PERCENTAGE_VARS) / total_assignments}\nk: {k}"
            )
            print(f"total_assignments + V_A = {total_assignments + PERCENTAGE_VARS * VAR_DECL_HAS_INIT}\tpercentage_input = {percentage_input}")
        elif args.vars:
            PERCENTAGE_VARS = percentage_input
            # the rest is correct
        else:
            # k : PERCENTAGE_FUNC_CALLS / 0.5 PERCENTAGE_ASSIGNMENTS = 0.35 / 0.225 ~ 3/2
            # values from "else" condition below
            k = (ASSIGN_HAS_FUNC_CALL * PERCENTAGE_ASSIGNMENTS) / PERCENTAGE_FUNC_CALLS
            # find the percentage of percentage_input that goes in PERCENTAGE_FUNC_CALLS and in PERCENTAGE_ASSIGNMENTS
            # we want k * PERCENTAGE_FUNC_CALLS + PERCENTAGE_FUNC_CALLS = percentage_input
            normalized_func_calls = PERCENTAGE_FUNC_CALLS * (1 - PERCENTAGE_VARS)

            normalized_vars = PERCENTAGE_VARS / (1 - normalized_func_calls)
            normalized_assigns = (PERCENTAGE_ASSIGNMENTS * (1 - PERCENTAGE_VARS)) / (
                1 - normalized_func_calls
            )
            normalized_if_elses = (PERCENTAGE_IF_ELSE * (1 - PERCENTAGE_VARS)) / (
                1 - normalized_func_calls
            )
            normalized_whiles = (PERCENTAGE_WHILE * (1 - PERCENTAGE_VARS)) / (
                1 - normalized_func_calls
            )

            PERCENTAGE_FUNC_CALLS = percentage_input / (k + 1)
            PERCENTAGE_VARS = normalized_vars * (1 - PERCENTAGE_FUNC_CALLS)
            PERCENTAGE_ASSIGNMENTS = (
                normalized_assigns * (1 - PERCENTAGE_FUNC_CALLS)
            ) / (1 - PERCENTAGE_VARS)
            PERCENTAGE_IF_ELSE = (normalized_if_elses * (1 - PERCENTAGE_FUNC_CALLS)) / (
                1 - PERCENTAGE_VARS
            )
            PERCENTAGE_WHILE = (normalized_whiles * (1 - PERCENTAGE_FUNC_CALLS)) / (
                1 - PERCENTAGE_VARS
            )
            PERCENTAGE_FUNC_CALLS = PERCENTAGE_FUNC_CALLS / (1 - PERCENTAGE_VARS)

            assignments_with_func_calls = k * PERCENTAGE_FUNC_CALLS
            ASSIGN_HAS_FUNC_CALL = assignments_with_func_calls / PERCENTAGE_ASSIGNMENTS

            print(
                f"Vars:\t{PERCENTAGE_VARS}\nAssignments:\t{PERCENTAGE_ASSIGNMENTS}\nIfElse:\t{PERCENTAGE_IF_ELSE}\nWhile:\t{PERCENTAGE_WHILE}\nFunction calls:\t{PERCENTAGE_FUNC_CALLS}"
            )
            print(f"Percentage function calls in assignments:\t{ASSIGN_HAS_FUNC_CALL}")
            print(
                f"Total:\t{PERCENTAGE_ASSIGNMENTS + PERCENTAGE_IF_ELSE + PERCENTAGE_WHILE + PERCENTAGE_FUNC_CALLS}"
            )
            print(
                f"A_F / F: {(ASSIGN_HAS_FUNC_CALL * PERCENTAGE_ASSIGNMENTS) / PERCENTAGE_FUNC_CALLS}\nk: {k}"
            )

    PERCENTAGE_FUNC_HEADERS = 0.02
    PERCENTAGE_IF_ELSE += PERCENTAGE_ASSIGNMENTS
    PERCENTAGE_WHILE += PERCENTAGE_IF_ELSE
    PERCENTAGE_FUNC_CALLS += PERCENTAGE_WHILE

    global lines_counter, func_args_dict, func_return_dict, indirections_to_var, var_to_indirection
    global MAX_NUM_INDIRECTIONS
    func_args_dict = {}

    MAX_NUM_INDIRECTIONS = 3
    func_return_dict = {1: [], 2: [], 3: []}
    indirections_to_var = {1: [], 2: [], 3: []}

    var_to_indirection = {}

    file_name = args.name
    if not file_name.endswith(".c") and not file_name.endswith(".cpp"):
        file_name += ".cpp"

    return file_name, program_size


def main():
    directory = "./gen_tests"
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_name, program_size = parse_args()
    file_path = os.path.join(directory, file_name)

    global program, lines_counter
    program = '#define $(l) [[clang::annotate_type("lifetime", #l)]]\n'
    lines_counter += 1

    for i in range(NUM_LIFETIMES):
        lifetime = chr(ord("a") + i)
        program += f"#define ${lifetime} $({lifetime})\n"

    lines_counter += NUM_LIFETIMES

    func_headers, num_funcs = createFunctionHeaders(program_size)
    program += func_headers
    program += createFunction(num_funcs + 1, program_size)

    with open(file_path, "w") as f:
        f.write(program)

    print(f"Successfully wrote test to {file_path}")
    print(f"Number of lines: {lines_counter}")


if __name__ == "__main__":
    main()
