from pprint import pprint

from app.news_parser import collect_from_all_sources


def main() -> None:
    """
    Запускает сбор новостей со всех источников и выводит краткую сводку в консоль.
    """
    items = collect_from_all_sources()
    print(f"Всего новостей: {len(items)}")
    if items:
        print("Первые 5 новостей:")
        pprint(items[:5])


if __name__ == "__main__":
    main()

