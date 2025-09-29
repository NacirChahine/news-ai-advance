// Article Likes/Dislikes JavaScript
// Handles AJAX functionality for article like/dislike actions

$(document).ready(function() {
    // Get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    const csrftoken = getCookie('csrftoken');
    
    // Setup AJAX to include CSRF token
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    
    // Handle like button clicks
    $(document).on('click', '.like-article-btn', function(e) {
        e.preventDefault();
        
        const btn = $(this);
        const articleId = btn.data('article-id');
        const likeUrl = btn.data('like-url');
        const container = btn.closest('.article-likes-container');
        const dislikeBtn = container.find('.dislike-article-btn');
        
        // Determine action based on current state
        const isActive = btn.hasClass('active');
        const action = isActive ? 'remove' : 'like';
        
        $.ajax({
            url: likeUrl,
            type: 'POST',
            data: {
                'article_id': articleId,
                'action': action
            },
            success: function(data) {
                if (data.success) {
                    // Update like count
                    container.find('.like-count').text(data.like_count);
                    
                    // Update dislike count
                    container.find('.dislike-count').text(data.dislike_count);
                    
                    // Update button states based on user_action
                    if (data.user_action === 'like') {
                        // User liked the article
                        btn.addClass('active');
                        btn.find('i').removeClass('far').addClass('fas');
                        dislikeBtn.removeClass('active');
                        dislikeBtn.find('i').removeClass('fas').addClass('far');
                    } else if (data.user_action === 'dislike') {
                        // User switched from like to dislike (shouldn't happen with like button, but handle it)
                        btn.removeClass('active');
                        btn.find('i').removeClass('fas').addClass('far');
                        dislikeBtn.addClass('active');
                        dislikeBtn.find('i').removeClass('far').addClass('fas');
                    } else {
                        // User removed their like
                        btn.removeClass('active');
                        btn.find('i').removeClass('fas').addClass('far');
                    }
                }
            },
            error: function(xhr, status, error) {
                console.error('Error liking article:', error);
                if (xhr.status === 401) {
                    alert('Please log in to like articles.');
                } else {
                    alert('There was an error processing your request. Please try again.');
                }
            }
        });
    });
    
    // Handle dislike button clicks
    $(document).on('click', '.dislike-article-btn', function(e) {
        e.preventDefault();
        
        const btn = $(this);
        const articleId = btn.data('article-id');
        const likeUrl = btn.data('like-url');
        const container = btn.closest('.article-likes-container');
        const likeBtn = container.find('.like-article-btn');
        
        // Determine action based on current state
        const isActive = btn.hasClass('active');
        const action = isActive ? 'remove' : 'dislike';
        
        $.ajax({
            url: likeUrl,
            type: 'POST',
            data: {
                'article_id': articleId,
                'action': action
            },
            success: function(data) {
                if (data.success) {
                    // Update like count
                    container.find('.like-count').text(data.like_count);
                    
                    // Update dislike count
                    container.find('.dislike-count').text(data.dislike_count);
                    
                    // Update button states based on user_action
                    if (data.user_action === 'dislike') {
                        // User disliked the article
                        btn.addClass('active');
                        btn.find('i').removeClass('far').addClass('fas');
                        likeBtn.removeClass('active');
                        likeBtn.find('i').removeClass('fas').addClass('far');
                    } else if (data.user_action === 'like') {
                        // User switched from dislike to like (shouldn't happen with dislike button, but handle it)
                        btn.removeClass('active');
                        btn.find('i').removeClass('fas').addClass('far');
                        likeBtn.addClass('active');
                        likeBtn.find('i').removeClass('far').addClass('fas');
                    } else {
                        // User removed their dislike
                        btn.removeClass('active');
                        btn.find('i').removeClass('fas').addClass('far');
                    }
                }
            },
            error: function(xhr, status, error) {
                console.error('Error disliking article:', error);
                if (xhr.status === 401) {
                    alert('Please log in to dislike articles.');
                } else {
                    alert('There was an error processing your request. Please try again.');
                }
            }
        });
    });
});

