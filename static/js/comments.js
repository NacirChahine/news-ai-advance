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

  const section = document.getElementById('comments-section');
  if(!section){ return; }
  const articleId = section.dataset.articleId;
  const listUrl = section.dataset.listUrl;
  const listEl = document.getElementById('comments-list');
  const pagerEl = document.getElementById('comments-pagination');

  async function fetchComments(page=1){
    listEl.innerHTML = '<div class="text-center text-muted py-3">Loading comments…</div>';
    try{
      const res = await fetch(`${listUrl}?page=${page}`);
      const data = await res.json();
      renderComments(data, page);
    }catch(e){
      listEl.innerHTML = '<div class="alert alert-danger">Failed to load comments.</div>';
    }
  }

  function renderComments(data, page){
    listEl.innerHTML = '';
    data.results.forEach(c => listEl.appendChild(renderCommentItem(c)));
    renderPagination(data, page);
  }

  function renderCommentItem(c, isReply=false){
    const item = el(`<div class="list-group-item ${isReply? 'ms-4' : ''}" data-comment-id="${c.id}">
      <div class="d-flex justify-content-between align-items-start">
        <div>
          <strong>${escapeHtml(c.user.username)}</strong>
          <small class="text-muted ms-2">${new Date(c.created_at).toLocaleString()}</small>
          ${c.is_edited ? '<small class="text-muted ms-1">(edited)</small>' : ''}
          <div class="mt-1">${escapeHtml(c.content)}</div>
        </div>
        <div class="ms-2 btn-group btn-group-sm">
          ${c.can_moderate ? `<button class="btn btn-outline-danger js-mod" data-remove="${!c.is_removed_moderator}">${c.is_removed_moderator? 'Restore' : 'Remove'}</button>` : ''}
          ${c.can_edit ? '<button class="btn btn-outline-secondary js-edit">Edit</button>' : ''}
          ${c.can_delete ? '<button class="btn btn-outline-secondary js-del">Delete</button>' : ''}
          <button class="btn btn-outline-secondary js-reply">Reply</button>
          <button class="btn btn-outline-secondary js-flag">Flag</button>
        </div>
      </div>
      <div class="replies mt-2"></div>
    </div>`);

    // Render nested replies if included
    if(c.replies && c.replies.length){
      const holder = item.querySelector('.replies');
      c.replies.forEach(r => holder.appendChild(renderCommentItem(r, true)));
    }

    bindItemActions(item, c);
    return item;
  }

  function bindItemActions(item, c){
    const replyBtn = item.querySelector('.js-reply');
    if(replyBtn){ replyBtn.addEventListener('click', () => showReplyForm(item, c)); }

    const editBtn = item.querySelector('.js-edit');
    if(editBtn){ editBtn.addEventListener('click', () => showEditForm(item, c)); }

    const delBtn = item.querySelector('.js-del');
    if(delBtn){ delBtn.addEventListener('click', () => deleteComment(c.id)); }

    const flagBtn = item.querySelector('.js-flag');
    if(flagBtn){ flagBtn.addEventListener('click', () => flagComment(c.id)); }

    const modBtn = item.querySelector('.js-mod');
    if(modBtn){ modBtn.addEventListener('click', () => moderateComment(c.id, modBtn.dataset.remove==='true')); }
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
    const contentDiv = item.querySelector('.mt-1');
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
        } else { alert(data.error || 'Failed to post'); }
      }catch(err){ alert('Failed to post'); }
    });
  }

  fetchComments(1);
})();

