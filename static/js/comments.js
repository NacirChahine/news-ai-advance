(function(){
  function getCookie(name){
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }
  function csrfHeader(){
    const csrftoken = getCookie('csrftoken');
    return csrftoken ? { 'X-CSRFToken': csrftoken } : {};
  }
  function el(html){
    const div = document.createElement('div');
    div.innerHTML = html.trim();
    return div.firstChild;
  }

  function timeAgo(date){
    const now = new Date();
    let diff = Math.floor((now - date) / 1000); // seconds
    if (isNaN(diff)) return '';
    // Future dates or negative -> treat as just now

    if (diff < 0) diff = 0;
    const mins = Math.floor(diff/60);
    const hours = Math.floor(diff/3600);
    const days = Math.floor(diff/86400);
    const weeks = Math.floor(diff/604800);
    if (diff < 60) return 'just now';
    if (mins < 60) return `${mins} min${mins!==1?'s':''} ago`;
    if (hours < 24) return `${hours} hour${hours!==1?'s':''} ago`;
    if (days < 7) return `${days} day${days!==1?'s':''} ago`;
    if (weeks < 5) return `${weeks} week${weeks!==1?'s':''} ago`;
    // Fallback to absolute for very old
    return date.toLocaleDateString();
  }

  const section = document.getElementById('comments-section');
  let currentPage = 1;
  let resizeTimer = null;

  if(!section){ return; }
  const articleId = section.dataset.articleId;
  const listUrl = section.dataset.listUrl;
  const listEl = document.getElementById('comments-list');
  const pagerEl = document.getElementById('comments-pagination');

  async function fetchComments(page=1){
    currentPage = page;
    listEl.innerHTML = '<div class="text-center text-muted py-3">Loading comments…</div>';
    try{
      const res = await fetch(`${listUrl}?page=${page}`);
      const data = await res.json();
      renderComments(data, page);
    }catch(e){
      listEl.innerHTML = '<div class="alert alert-danger">Failed to load comments.</div>';
    }
  }

  function initTooltips(scope){
    try{
      if(window.bootstrap && bootstrap.Tooltip){
        const els = (scope || document).querySelectorAll('[data-bs-toggle="tooltip"]');
        els.forEach(el => {
          const existing = bootstrap.Tooltip.getInstance(el);
          if(!existing){
            new bootstrap.Tooltip(el, { container: 'body' });
          } else {
            // Ensure updated title is used on next show without re-instantiating
            const t = el.getAttribute('title');
            if(t){ el.setAttribute('data-bs-original-title', t); }
            existing.update();
          }
        });
      }
    }catch(e){ /* no-op if bootstrap not available */ }
  }

  function renderComments(data, page){
    listEl.innerHTML = '';
    data.results.forEach(c => listEl.appendChild(renderCommentItem(c)));
    // Initialize tooltips for newly inserted elements
    initTooltips(listEl);
    renderPagination(data, page);
  }

  function renderCommentItem(c, isReply=false){
    const isAuthed = section.dataset.authenticated === 'true';
    const depthClass = `depth-${Math.min(c.depth || 0, 6)}`;
    const created = new Date(c.created_at);
    const rel = timeAgo(created);
    const abs = created.toLocaleString();

    const upActive = c.user_vote === 1 ? 'active' : '';
    const downActive = c.user_vote === -1 ? 'active' : '';
    const scoreText = (typeof c.score === 'number') ? c.score : 0;
    const voteBlock = `
      <div class="vote-block d-flex flex-column align-items-center me-2">
        ${isAuthed ? `<button class="btn btn-sm btn-link text-decoration-none js-upvote ${upActive}" aria-label="Upvote" data-bs-toggle="tooltip" data-bs-placement="right" title="Upvote this comment"><i class=\"fa-solid fa-caret-up\"></i></button>` : '<span class="opacity-50" data-bs-toggle="tooltip" data-bs-placement="right" title="Log in to vote"><i class="fa-solid fa-caret-up"></i></span>'}
        <div class="comment-score" aria-live="polite" data-bs-toggle="tooltip" data-bs-placement="right" title="Score: ${scoreText} (upvotes minus downvotes)">${scoreText}</div>
        ${isAuthed ? `<button class="btn btn-sm btn-link text-decoration-none js-downvote ${downActive}" aria-label="Downvote" data-bs-toggle="tooltip" data-bs-placement="right" title="Downvote this comment"><i class=\"fa-solid fa-caret-down\"></i></button>` : '<span class="opacity-50" data-bs-toggle="tooltip" data-bs-placement="right" title="Log in to vote"><i class="fa-solid fa-caret-down"></i></span>'}
      </div>`;

    const actionsDropdown = `
      <div class="btn-group">
        <button type="button" class="btn btn-sm btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false" aria-label="More comment actions">
          <i class="fa-solid fa-ellipsis-vertical"></i>
        </button>
        <ul class="dropdown-menu">
          ${c.can_edit ? '<li><a class="dropdown-item js-edit" href="#">Edit</a></li>' : ''}
          ${c.can_delete ? '<li><a class="dropdown-item text-danger js-del" href="#">Delete</a></li>' : ''}
          <li><a class="dropdown-item js-flag" href="#">Flag</a></li>
          ${c.can_moderate ? `<li><a class="dropdown-item js-mod" href="#" data-remove="${!c.is_removed_moderator}">${c.is_removed_moderator? 'Restore (Moderator)' : 'Remove (Moderator)'}</a></li>` : ''}
        </ul>
      </div>`;

    const item = el(`<div class="list-group-item comment-item ${depthClass}" data-comment-id="${c.id}">
      <div class="thread-left-gutter" role="button" aria-label="Toggle thread" tabindex="0"></div>
      <button type="button" class="thread-collapse-indicator" aria-expanded="true" aria-label="Collapse thread" title="Collapse thread">−</button>
      <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
        ${voteBlock}
        <div class="flex-grow-1 min-w-0">
          <strong class="text-truncate">${escapeHtml(c.user.username)}</strong>
          <small class="text-muted ms-2" title="${abs}">${rel}</small>
          ${c.is_edited ? '<small class="text-muted ms-1">(edited)</small>' : ''}
          <div class="mt-1 comment-content">${escapeHtml(c.content)}</div>
          ${isAuthed ? `<div class="comment-actions mt-2">${(c.depth || 0) < 5 ? '<button class="btn btn-sm btn-outline-primary js-reply" aria-label="Reply to comment"><i class=\"fa-regular fa-comment-dots me-1\"></i>Reply</button>' : ''} ${actionsDropdown}</div>` : ''}
        </div>
      </div>
      <div class="replies mt-2"></div>
      ${c.replies && c.replies.length ? `<button class="btn btn-sm btn-link text-decoration-none px-0 js-toggle-replies" aria-expanded="true">Hide replies (${c.replies.length})</button>` : ''}
    </div>`);

    // Render nested replies if included
    if(c.replies && c.replies.length){
      const holder = item.querySelector('.replies');
      c.replies.forEach(r => holder.appendChild(renderCommentItem(r, true)));
    }

    setupThreadControls(item);
    bindItemActions(item, c);
    return item;
  }

  function bindItemActions(item, c){
    const replyBtn = item.querySelector('.js-reply');
    if(replyBtn){ replyBtn.addEventListener('click', () => showReplyForm(item, c)); }

    const editBtn = item.querySelector('.js-edit');
    if(editBtn){ editBtn.addEventListener('click', (e)=>{ e.preventDefault(); showEditForm(item, c); }); }

    const delBtn = item.querySelector('.js-del');
    if(delBtn){ delBtn.addEventListener('click', (e)=>{ e.preventDefault(); deleteComment(c.id); }); }

    const flagBtn = item.querySelector('.js-flag');
    if(flagBtn){ flagBtn.addEventListener('click', (e)=>{ e.preventDefault(); flagComment(c.id); }); }

    const modBtn = item.querySelector('.js-mod');
    if(modBtn){ modBtn.addEventListener('click', (e)=>{ e.preventDefault(); moderateComment(c.id, modBtn.dataset.remove==='true'); }); }

    const toggleBtn = item.querySelector('.js-toggle-replies');
    const upBtn = item.querySelector('.js-upvote');
    const downBtn = item.querySelector('.js-downvote');
    if(upBtn){ upBtn.addEventListener('click', async (e)=>{ e.preventDefault(); await handleVote(c.id, 1, item); }); }
    if(downBtn){ downBtn.addEventListener('click', async (e)=>{ e.preventDefault(); await handleVote(c.id, -1, item); }); }

    if(toggleBtn){
      const holder = item.querySelector('.replies');
      toggleBtn.addEventListener('click', (e)=>{
        e.preventDefault();
        const collapsed = item.classList.contains('collapsed');
        toggleThread(item, !collapsed);
        toggleBtn.setAttribute('aria-expanded', (!item.classList.contains('collapsed')).toString());
        toggleBtn.textContent = (item.classList.contains('collapsed') ? 'Show replies' : 'Hide replies') + (holder.children.length ? ` (${holder.children.length})` : '');
      });
    }
  }

  function toggleThread(item, collapse){
    const holder = item.querySelector('.replies');
    const shouldCollapse = (typeof collapse === 'boolean') ? collapse : !item.classList.contains('collapsed');
    item.classList.toggle('collapsed', shouldCollapse);
    if(holder){ holder.style.display = shouldCollapse ? 'none' : ''; }
    const indicator = item.querySelector('.thread-collapse-indicator');
    if(indicator){
      indicator.textContent = shouldCollapse ? '+' : '\u2212';
      indicator.setAttribute('aria-expanded', (!shouldCollapse).toString());
      indicator.setAttribute('aria-label', shouldCollapse ? 'Expand thread' : 'Collapse thread');
      indicator.setAttribute('title', shouldCollapse ? 'Expand thread' : 'Collapse thread');
    }
  }

  function setupThreadControls(item){
    const gutter = item.querySelector('.thread-left-gutter');
    const indicator = item.querySelector('.thread-collapse-indicator');
    const borderColor = getComputedStyle(item).borderLeftColor;
    if(indicator){
      indicator.style.borderColor = borderColor;
      indicator.style.color = borderColor;
      indicator.addEventListener('click', (e)=>{ e.preventDefault(); e.stopPropagation(); toggleThread(item); });
      indicator.addEventListener('keydown', (e)=>{ if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); toggleThread(item); } });
    }
    if(gutter){
      gutter.addEventListener('click', (e)=>{ e.preventDefault(); toggleThread(item); });
      gutter.addEventListener('keydown', (e)=>{ if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); toggleThread(item); } });
    }
  }


  function renderPagination(data, page){
    pagerEl.innerHTML = '';
    const makePage = (p, label, disabled=false, active=false) => {
      const li = el(`<li class="page-item ${disabled? 'disabled':''} ${active? 'active':''}"><a class="page-link" href="#">${label}</a></li>`);
      if(!disabled){ li.addEventListener('click', e => { e.preventDefault(); fetchComments(p); }); }
      return li;
    };
    pagerEl.appendChild(makePage(Math.max(1, page-1), 'Prev', page<=1));
    for(let p=1; p<=data.num_pages; p++){
      pagerEl.appendChild(makePage(p, p, false, p===page));
    }
    pagerEl.appendChild(makePage(Math.min(data.num_pages, page+1), 'Next', page>=data.num_pages));
  }

  function showReplyForm(item, c){
    const holder = item.querySelector('.replies');
    const existing = holder.querySelector('.reply-form');
    if(existing){ existing.remove(); }
    const form = el(`<form class="reply-form mt-2">
      <div class="mb-2"><textarea class="form-control" rows="2" maxlength="5000" placeholder="Write a reply..."></textarea></div>
      <button class="btn btn-primary btn-sm">Reply</button>
    </form>`);
    form.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const content = form.querySelector('textarea').value.trim();
      if(!content) return;
      try{
        const res = await fetch(`/news/comments/${c.id}/reply/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded', ...csrfHeader() },
          body: new URLSearchParams({ content })
        });
        const data = await res.json();
        if(res.ok){
          holder.prepend(renderCommentItem(data.comment, true));
          form.remove();
        }else{ alert(data.error || 'Failed to reply'); }
      }catch(err){ alert('Failed to reply'); }
    });
    holder.prepend(form);
  }

  function showEditForm(item, c){
    const contentDiv = item.querySelector('.comment-content');
    const original = contentDiv.textContent;
    contentDiv.innerHTML = '';
    const form = el(`<form class="edit-form"><div class="mb-2"><textarea class="form-control" rows="3" maxlength="5000">${escapeHtml(original)}</textarea></div><button class="btn btn-primary btn-sm">Save</button> <button class="btn btn-link btn-sm">Cancel</button></form>`);
    const [saveBtn, cancelBtn] = form.querySelectorAll('button');
    form.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const content = form.querySelector('textarea').value.trim();
      if(!content) return;
      try{
        const res = await fetch(`/news/comments/${c.id}/edit/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded', ...csrfHeader() },
          body: new URLSearchParams({ content })
        });
        const data = await res.json();
        if(res.ok){ contentDiv.textContent = data.comment.content; }
        else{ alert(data.error || 'Failed to edit'); contentDiv.textContent = original; }
      }catch(err){ alert('Failed to edit'); contentDiv.textContent = original; }
    });
    cancelBtn.addEventListener('click', (e)=>{ e.preventDefault(); contentDiv.textContent = original; });
    contentDiv.appendChild(form);
  }

  async function deleteComment(id){
    if(!confirm('Delete this comment?')) return;
    try{
      const res = await fetch(`/news/comments/${id}/`, { method: 'POST', headers: { ...csrfHeader() } });
      const data = await res.json();
      if(res.ok){
        const item = listEl.querySelector(`[data-comment-id="${id}"]`);
        if(item){ item.querySelector('.mt-1').textContent = data.comment.content; }
      } else { alert(data.error || 'Failed to delete'); }
    }catch(err){ alert('Failed to delete'); }
  }

  async function handleVote(commentId, value, item){
    const isAuthed = section.dataset.authenticated === 'true';
    if(!isAuthed){ alert('Please log in to vote.'); return; }
    const upBtn = item.querySelector('.js-upvote');
    const downBtn = item.querySelector('.js-downvote');
    const scoreEl = item.querySelector('.comment-score');
    const upActive = upBtn && upBtn.classList.contains('active');
    const downActive = downBtn && downBtn.classList.contains('active');

    let method = 'POST';
    let body = undefined;
    if(value === 1){
      if(upActive){ method = 'DELETE'; }
      else if(downActive){ method = 'PUT'; body = new URLSearchParams({ value: '1' }); }
      else { method = 'POST'; body = new URLSearchParams({ value: '1' }); }
    } else if(value === -1){
      if(downActive){ method = 'DELETE'; }
      else if(upActive){ method = 'PUT'; body = new URLSearchParams({ value: '-1' }); }
      else { method = 'POST'; body = new URLSearchParams({ value: '-1' }); }
    }

    try{
      const res = await fetch(`/news/comments/${commentId}/vote/`, {
        method,
        headers: { ...(body ? { 'Content-Type': 'application/x-www-form-urlencoded' } : {}), ...csrfHeader() },
        body
      });
      const data = await res.json();
      if(!res.ok){ throw new Error(data.error || 'Vote failed'); }
      // Update UI
      if(scoreEl){
        const s = (typeof data.score === 'number') ? data.score : 0;
        scoreEl.textContent = s;
        const title = `Score: ${s} (upvotes minus downvotes)`;
        scoreEl.setAttribute('title', title);
        // Update Bootstrap tooltip content without re-instantiation
        if(window.bootstrap && bootstrap.Tooltip){
          const inst = bootstrap.Tooltip.getInstance(scoreEl);
          if(inst){ scoreEl.setAttribute('data-bs-original-title', title); inst.update(); }
        }
      }
      if(upBtn){ upBtn.classList.toggle('active', data.user_vote === 1); }
      if(downBtn){ downBtn.classList.toggle('active', data.user_vote === -1); }
      // Do not re-initialize tooltips to avoid flicker
    }catch(err){
      alert(err.message || 'Vote failed');
    }
  }

  async function moderateComment(id, remove){
    try{
      const res = await fetch(`/news/comments/${id}/moderate/`, {
        method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded', ...csrfHeader() },
        body: new URLSearchParams({ remove })
      });
      const data = await res.json();
      if(res.ok){ fetchComments(1); }
      else { alert(data.error || 'Moderation failed'); }
    }catch(err){ alert('Moderation failed'); }
  }

  async function flagComment(id){
    const reason = prompt('Reason for flagging? (spam, abuse, hate, other)', 'other') || 'other';
    try{
      const res = await fetch(`/news/comments/${id}/flag/`, {
        method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded', ...csrfHeader() },
        body: new URLSearchParams({ reason })
      });
      if(res.ok){ alert('Flag submitted'); } else { alert('Failed to flag'); }
    }catch(err){ alert('Failed to flag'); }
  }

  function escapeHtml(str){
    return str.replace(/[&<>"]?/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]||c;
    });
  }

  // Create comment
  const form = document.getElementById('comment-create-form');
  if(form){
    form.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const content = document.getElementById('comment-content').value.trim();
      if(!content) return;
      try{
        const res = await fetch(listUrl, {
          method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded', ...csrfHeader() },
          body: new URLSearchParams({ content })
        });
        const data = await res.json();
        if(res.ok){
          document.getElementById('comment-content').value='';
          listEl.prepend(renderCommentItem(data.comment));
          initTooltips(listEl);
        } else { alert(data.error || 'Failed to post'); }
      }catch(err){ alert('Failed to post'); }
    });
  }

  // Re-render actions layout on resize (debounced)
  window.addEventListener('resize', ()=>{
    if(resizeTimer){ clearTimeout(resizeTimer); }
    resizeTimer = setTimeout(()=>{ fetchComments(currentPage); }, 250);
  });

  fetchComments(1);
})();

