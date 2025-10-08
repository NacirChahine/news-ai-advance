// Article Actions JavaScript
// Handles AJAX functionality for article actions like save/unsave

$(document).ready(function() {
    // Setup CSRF token for AJAX requests
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
    
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    
    // Handle save/unsave article button clicks
    $(document).on('click', '.save-article-btn', function(e) {
        e.preventDefault();
        e.stopPropagation(); // Prevent card click when clicking save button
        
        const btn = $(this);
        const articleId = btn.data('article-id');
        const saveUrl = btn.data('save-url');
        
        $.ajax({
            url: saveUrl,
            type: 'POST',
            data: {
                'article_id': articleId
            },
            success: function(data) {
                // Update button appearance based on saved status
                if (data.saved) {
                    // Article was saved
                    btn.removeClass('btn-outline-primary btn-outline-light').addClass('btn-danger');
                    btn.find('i').removeClass('far fa-bookmark').addClass('fas fa-bookmark');
                    btn.attr('title', 'Unsave article');
                    btn.attr('aria-label', 'Unsave article');
                    if (btn.find('span').length) {
                        btn.find('span').text('Unsave');
                    }
                } else {
                    // Article was unsaved
                    btn.removeClass('btn-danger').addClass('btn-outline-light');
                    btn.find('i').removeClass('fas fa-bookmark').addClass('far fa-bookmark');
                    btn.attr('title', 'Save article');
                    btn.attr('aria-label', 'Save article');
                    if (btn.find('span').length) {
                        btn.find('span').text('Save');
                    }
                }
                
                // If we're on the saved articles page and unsaving, remove the row
                if (!data.saved && btn.hasClass('remove-saved-btn')) {
                    btn.closest('tr').fadeOut(300, function() {
                        $(this).remove();
                        
                        // Update the count of saved articles
                        const count = $('.saved-article-row').length;
                        $('.saved-count').text(count + ' saved article' + (count !== 1 ? 's' : ''));
                        
                        // If no articles left, show the empty state
                        if (count === 0) {
                            $('.saved-articles-table').hide();
                            $('.saved-articles-empty').removeClass('d-none').show();
                            $('.card-footer').hide();
                        }
                    });
                }
            },
            error: function(xhr, status, error) {
                console.error('Error saving/unsaving article:', error);
                alert('There was an error processing your request. Please try again.');
            }
        });
    });
});