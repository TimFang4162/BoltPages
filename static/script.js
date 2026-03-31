document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const container = btn.closest('.highlight-container');
      if (!container) return;
      const preEl = container.querySelector('.highlight-content pre');
      if (!preEl) return;
      const clone = preEl.cloneNode(true);
      clone.querySelectorAll('.linenos').forEach(el => el.remove());

      let codeText = clone.textContent.trim();
      codeText = codeText.replace(/\n\s*\n/g, '\n');

      navigator.clipboard.writeText(codeText);
      btn.innerHTML='<span class="icon--mdi icon--mdi--tick icon_14px"></span>已复制'
      setTimeout(() => btn.innerHTML = '<span class="icon--mdi icon--mdi--content-copy icon_14px"></span>复制', 2000);
    });
  });

  document.querySelector('.theme-toggle')?.addEventListener('click', () => {
    console.log('Theme toggle clicked');
    var savedTheme = localStorage.getItem('theme');
    var newTheme = (savedTheme === 'dark') ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  });

  const headings = document.querySelectorAll('h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]');
  const tocLinks = document.querySelectorAll('.toc-item a');

  if (headings.length > 0 && tocLinks.length > 0) {
    let currentActiveId = '';

    function updateActiveHeading() {
      const scrollY = window.scrollY;
      const windowHeight = window.innerHeight;
      
      let closestHeading = null;
      let minDistance = Infinity;

      headings.forEach(heading => {
        const rect = heading.getBoundingClientRect();
        const headingTop = rect.top + scrollY;
        const distance = Math.abs(headingTop - (scrollY + 100));

        if (rect.top <= windowHeight * 0.3 && distance < minDistance) {
          minDistance = distance;
          closestHeading = heading;
        }
      });

      if (!closestHeading) {
        headings.forEach(heading => {
          const rect = heading.getBoundingClientRect();
          if (rect.top > 0) {
            if (!closestHeading || rect.top < closestHeading.getBoundingClientRect().top) {
              closestHeading = heading;
            }
          }
        });
      }

      const activeId = closestHeading?.id || '';
      if (activeId && activeId !== currentActiveId) {
        currentActiveId = activeId;
        tocLinks.forEach(link => {
          link.classList.remove('active');
          link.parentElement?.classList.remove('active');
        });

        const activeLink = document.querySelector(`.toc-item a[href="#${activeId}"]`);
        if (activeLink) {
          activeLink.classList.add('active');
          activeLink.parentElement?.classList.add('active');
          
          const tocList = document.querySelector('.toc-list');
          if (tocList) {
            const parent = activeLink.closest('.toc-item');
            if (parent) {
              const listRect = tocList.getBoundingClientRect();
              const parentRect = parent.getBoundingClientRect();
              const scrollTop = tocList.scrollTop;
              
              const parentTopInList = parentRect.top - listRect.top;
              const listHeight = listRect.height;
              const parentHeight = parentRect.height;
              
              if (parentTopInList < 50) {
                tocList.scrollTo({
                  top: scrollTop + parentTopInList - 50,
                  behavior: 'smooth'
                });
              } else if (parentTopInList > listHeight - parentHeight - 50) {
                tocList.scrollTo({
                  top: scrollTop + parentTopInList - listHeight + parentHeight + 50,
                  behavior: 'smooth'
                });
              }
            }
          }
        }
      }
    }

    let ticking = false;
    window.addEventListener('scroll', () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          updateActiveHeading();
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });

    updateActiveHeading();
  }

  window.copyHeadingLink = function(headingId) {
    const url = new URL(window.location.href);
    url.hash = headingId;
    navigator.clipboard.writeText(url.toString()).then(() => {
      const btn = document.querySelector(`#${headingId} .header-anchor-btn`);
      if (btn) {
        btn.innerHTML='<span class="icon--mdi icon--mdi--tick icon_14px"></span>'
        setTimeout(() => btn.innerHTML='#', 2000);
      }
    });
  };
});
