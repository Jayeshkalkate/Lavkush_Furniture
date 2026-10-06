(function(){
  const root=document.documentElement;
  const body=document.body;
  const stored=localStorage.getItem('lf-theme');
  if(stored==='dark'){root.setAttribute('data-theme','dark');body.classList.add('dark-mode');}
  document.querySelectorAll('.theme-toggle').forEach(btn=>btn.addEventListener('click',function(){
    const dark=root.getAttribute('data-theme')!=='dark';
    root.setAttribute('data-theme',dark?'dark':'light');
    body.classList.toggle('dark-mode',dark);
    localStorage.setItem('lf-theme',dark?'dark':'light');
    const icon=btn.querySelector('i'); if(icon) icon.className=dark?'fa-regular fa-sun':'fa-regular fa-moon';
  }));
  document.querySelectorAll('form[data-confirm]').forEach(form=>form.addEventListener('submit',function(e){
    if(!window.confirm(form.dataset.confirm)){e.preventDefault();}
  }));
  document.querySelectorAll('.alert').forEach((el)=>setTimeout(()=>{if(window.bootstrap){const inst=bootstrap.Alert.getOrCreateInstance(el);inst.close();}},7000));
})();
