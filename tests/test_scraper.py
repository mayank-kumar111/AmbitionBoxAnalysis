from src.scraper.ambitionbox_scraper import AmbitionBoxScraper


SAMPLE_HTML = """
<div class="companyCardWrapper__metaInformation">
  <h2>Example Corp</h2>
  <span class="companyCardWrapper__companyRatingValue">4.2</span>
  <span class="companyCardWrapper__interLinking">IT Services | 1k-5k Employees | Public | 20 years old | Jaipur +10 more</span>
</div>
"""


def test_parse_page_extracts_company_card():
    rows = AmbitionBoxScraper.parse_page(SAMPLE_HTML)

    assert rows == [
        {
            "company_name": "Example Corp",
            "company_rating": "4.2",
            "other_data": "IT Services, 1k-5k Employees, Public, 20 years old, Jaipur +10 more",
        }
    ]


def test_parse_page_handles_missing_fields():
    html = '<div class="companyCardWrapper__metaInformation"><h2>Example Corp</h2></div>'
    rows = AmbitionBoxScraper.parse_page(html)

    assert rows[0]["company_name"] == "Example Corp"
    assert rows[0]["company_rating"] is None
    assert rows[0]["other_data"] is None
