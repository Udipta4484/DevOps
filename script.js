document.addEventListener('DOMContentLoaded', () => {
    const blogPostForm = document.getElementById('blogPostForm');
    const blogPostList = document.getElementById('blogPostList');

    // Add a class to the body to trigger the smooth opening animation
    document.body.classList.add('loaded');

    // IMPORTANT: When deploying, this should be the private IP of your backend instance
    // that the FRONTEND EC2 instance can reach.

    const BACKEND_API_BASE_URL = 'http://localhost:5000';//for local hosting

    // Function to format date for display
    function formatDate(dateString) {
        const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true };
        return new Date(dateString).toLocaleDateString(undefined, options);
    }

    // Function to fetch and display blog posts
    async function fetchBlogPosts() {
        try {
            const response = await fetch(`${BACKEND_API_BASE_URL}/posts`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status} 😔`);
            }
            const posts = await response.json();
            blogPostList.innerHTML = ''; // Clear existing list

            if (posts.length === 0) {
                blogPostList.innerHTML = '<p class="no-posts-message">Looks like no one has shared their ink yet. Be the first! ✨</p>';
            } else {
                // Sort posts by creation date, newest first
                posts.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

                posts.forEach(post => {
                    const postDiv = document.createElement('div');
                    postDiv.classList.add('blog-post');
                    postDiv.innerHTML = `
                        <h3>${post.title}</h3>
                        <p class="author-info">By: ${post.author_name} (${post.author_email})</p>
                        <p>${post.content}</p>
                        <p class="post-date">Published on: ${formatDate(post.created_at)}</p>
                    `;
                    blogPostList.appendChild(postDiv);
                });
            }
        } catch (error) {
            console.error('Error fetching blog posts:', error);
            blogPostList.innerHTML = '<p class="no-posts-message">Oops! 😬 Error loading blog posts. Please check backend connection. Is the server running? 🧐</p>';
        }
    }

    // Function to handle form submission
    blogPostForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default form submission

        const authorName = document.getElementById('authorName').value;
        const authorEmail = document.getElementById('authorEmail').value;
        const blogTitle = document.getElementById('blogTitle').value;
        const blogContent = document.getElementById('blogContent').value;

        try {
            const response = await fetch(`${BACKEND_API_BASE_URL}/posts`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    author_name: authorName,
                    author_email: authorEmail,
                    title: blogTitle,
                    content: blogContent
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.error || errorData.message} 😓`);
            }

            const newPost = await response.json();
            console.log('Blog post added successfully! 🎉', newPost);

            // Clear form fields (except author name/email for convenience if user wants to post multiple times)
            document.getElementById('blogTitle').value = '';
            document.getElementById('blogContent').value = '';
            // If you want to clear all fields: blogPostForm.reset();

            // Refresh the blog post list
            fetchBlogPosts();

        } catch (error) {
            console.error('Error adding blog post:', error);
            alert(`Failed to publish post: ${error.message || 'Please try again. 😞'}`);
        }
    });

    // Initial fetch of blog posts when the page loads
    fetchBlogPosts();
});