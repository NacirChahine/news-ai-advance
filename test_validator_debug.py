from bs4 import BeautifulSoup
from news_aggregator.article_validator import ArticleValidator

html = """
<html>
<head>
    <title>Breaking News: Important Update</title>
    <meta property="og:type" content="article">
    <meta property="article:author" content="Jane Smith">
    <meta property="article:published_time" content="2024-11-29T10:00:00Z">
</head>
<body>
    <article>
        <h1>Breaking News: Important Update</h1>
        <div class="author">By Jane Smith</div>
        <time datetime="2024-11-29">November 29, 2024</time>
        <p>This is the first paragraph of the article with substantial content that provides important information to the readers.</p>
        <p>This is the second paragraph continuing the story with more details and context about the breaking news event.</p>
        <p>This is the third paragraph providing additional analysis and expert opinions on the matter.</p>
        <p>This is the fourth paragraph with concluding remarks and future implications of the news story.</p>
    </article>
</body>
</html>
"""

soup = BeautifulSoup(html, 'lxml')
validation = ArticleValidator.validate_article_structure(soup)

print("Validation Results:")
print(f"  Valid: {validation['is_valid']}")
print(f"  Has title: {validation['has_title']}")
print(f"  Has content: {validation['has_content']}")
print(f"  Has metadata: {validation['has_metadata']}")
print(f"  Has author: {validation['has_author']}")
print(f"  Has date: {validation['has_date']}")
print(f"  Word count: {validation['word_count']}")
print(f"  Paragraph count: {validation['paragraph_count']}")
print(f"  Reason: {validation.get('reason')}")
