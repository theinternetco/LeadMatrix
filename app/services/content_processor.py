"""
Content Processor - Blog to GMB conversion
"""

class ContentProcessor:
    @staticmethod
    def prepare_gmb_content(blog_post):
        """Convert blog post to GMB format"""
        post_content = f"{blog_post.title}\n\n"
        excerpt = blog_post.excerpt or blog_post.content[:250]
        post_content += f"{excerpt}...\n\n"
        post_content += "📖 Read the full article on our website!"
        
        if len(post_content) > 1500:
            post_content = post_content[:1497] + "..."
        
        return {
            'post_title': blog_post.title[:100],
            'post_content': post_content,
            'post_image_url': blog_post.featured_image_url,
            'cta_type': 'LEARN_MORE',
            'cta_url': blog_post.blog_url
        }


content_processor = ContentProcessor()
