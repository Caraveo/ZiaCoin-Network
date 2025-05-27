from colorama import init, Fore, Style
init(autoreset=True)

def print_success(message: str) -> None:
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_error(message: str) -> None:
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

def print_warning(message: str) -> None:
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")

def print_info(message: str) -> None:
    print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}") 