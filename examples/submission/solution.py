import sys


def main() -> None:
    values = [int(value) for value in sys.argv[1:]]
    print(sum(values))


if __name__ == "__main__":
    main()
