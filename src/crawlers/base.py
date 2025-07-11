from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class CompanyCrawler(ABC):
    """Abstract base class for company-specific crawlers."""
    def __init__(self, full_code: str, config: dict):
        self.full_code = full_code
        self.config = config

    @abstractmethod
    def crawl_quarterly_performance(
        self,
        keywords: List[str],
        output_dir: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, str]:
        """Crawl quarterly performance and return mapping of keyword to output file path."""
        pass

    @abstractmethod
    def crawl_company_announcements(
        self,
        keywords: List[str],
        output_dir: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, str]:
        """Crawl company announcements and return mapping of keyword to output file path."""
        pass

    def print_sections(self):
        """Print available sections."""
        print("Select report section(s), separated by comma:")
        for key, entry in self.SECTIONS.items():
            if len(entry) == 3:
                zh, en, _ = entry
                disp = f"{zh} ({en})"
            else:
                disp, _ = entry
            print(f"{key}. {disp}")

    def run_section(
        self,
        key: str,
        keywords: List[str],
        output_base: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        """Run a single section crawl."""
        if key not in self.SECTIONS:
            print(f"Unknown section '{key}', skipping.")
            return
        entry = self.SECTIONS[key]
        if len(entry) == 3:
            zh, en, method_name = entry
            dir_name = en
            disp = f"{zh} ({en})"
        else:
            disp, method_name = entry
            dir_name = disp
        from pathlib import Path
        import os

        output_dir = str(Path(output_base) / dir_name)
        os.makedirs(output_dir, exist_ok=True)
        fn = getattr(self, method_name)
        try:
            result = fn(keywords, output_dir=output_dir, start_date=start_date, end_date=end_date)
            if result:
                print(f"Generated {disp} docs:")
                for kw, path in result.items():
                    print(f"  {kw}: {path}")
            else:
                print(f"No {disp} docs generated.")
        except Exception as e:
            print(f"Error during {disp} crawl: {e}")
