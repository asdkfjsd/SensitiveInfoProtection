function toast(msg, type="info"){
  const box = document.createElement('div');
  box.className = `toast ${type}`;
  Object.assign(box.style, {
    position:'fixed', top:'16px', right:'16px', zIndex:2000,
    background: type==='error' ? '#ffe8e6' : '#eaffef',
    color: type==='error' ? '#7f1d1d' : '#065f46',
    borderLeft: `4px solid ${type==='error' ? '#dc2626' : '#16a34a'}`,
    padding:'10px 14px', borderRadius:'6px', boxShadow:'0 6px 18px rgba(0,0,0,.12)',
    transition:'all .25s'
  });
  box.textContent = msg;
  document.body.appendChild(box);
  setTimeout(()=>{ box.style.opacity='0'; box.style.transform='translateY(-6px)'; }, 2800);
  setTimeout(()=> box.remove(), 3200);
}

async function postFormByFetch(form){
  const fd = new FormData(form);
  const res = await fetch(form.action, {
    method: form.method || 'POST',
    headers: { 'X-Requested-With': 'XMLHttpRequest' }, // 让后端知道这是 AJAX
    body: fd
  });
  let data;
  try { data = await res.json(); } catch(e){ data = { ok:false, message:'响应解析失败'}; }
  if(!res.ok || !data.ok) throw new Error(data.message || '操作失败');
  return data;
}

function findRow(el){ return el.closest('tr[data-uid]'); }

document.addEventListener('submit', async (e)=>{
  const f = e.target;

  // 赋权
  if(f.matches('.js-grant')){
    e.preventDefault();
    try{
      const data = await postFormByFetch(f);
      const row = findRow(f);
      row.querySelector('.role-cell').textContent = (data.roles||[]).join(', ');
      toast(data.message || '赋权成功', 'success');
    }catch(err){ toast(err.message, 'error'); }
  }

  // 回收
  if(f.matches('.js-revoke')){
    e.preventDefault();
    try{
      const data = await postFormByFetch(f);
      const row = findRow(f);
      row.querySelector('.role-cell').textContent = (data.roles||[]).join(', ');
      toast(data.message || '回收成功', 'success');
    }catch(err){ toast(err.message, 'error'); }
  }

  // 重置密码
  if(f.matches('.js-reset')){
    e.preventDefault();
    try{
      const data = await postFormByFetch(f);
      f.querySelector('input[name="new_password"]').value = '';
      toast(data.message || '已重置密码', 'success');
    }catch(err){ toast(err.message, 'error'); }
  }

  // 删除
  if(f.matches('.js-delete')){
    e.preventDefault();
    if(!confirm('确认删除该用户？该操作不可撤销')) return;
    try{
      const data = await postFormByFetch(f);
      const row = findRow(f);
      row.remove();
      toast(data.message || '已删除', 'success');
    }catch(err){ toast(err.message, 'error'); }
  }
});
