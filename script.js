document.addEventListener('DOMContentLoaded', () => {
    const newsGrid = document.getElementById('news-grid');
    const lastUpdatedSpan = document.getElementById('last-updated');
    const filterBtns = document.querySelectorAll('.filter-btn');

    let allNews = [];

    // Helper: Format relative time
    function timeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        let interval = seconds / 31536000;

        if (interval > 1) return Math.floor(interval) + " years ago";
        interval = seconds / 2592000;
        if (interval > 1) return Math.floor(interval) + " months ago";
        interval = seconds / 86400;
        if (interval > 1) return Math.floor(interval) + " days ago";
        interval = seconds / 3600;
        if (interval > 1) return Math.floor(interval) + " hours ago";
        interval = seconds / 60;
        if (interval > 1) return Math.floor(interval) + " minutes ago";
        return Math.floor(seconds) + " seconds ago";
    }

    // Default image if missing (Generic Fallback)
    const DEFAULT_IMG = 'https://source.unsplash.com/800x600/?news,maharashtra,newspaper';

    // Source-specific Logo Fallbacks
    const SOURCE_LOGOS = {
        "ABP Majha": "https://static.abplive.com/frontend/images/abp_logo_header.png",
        "Lokmat": "https://m.lokmat.com/assets/images/lokmat-logo.png",
        "Dainik Pudhari": "https://pudhari.news/static/img/logo.png?v=1",
        "Pudhari": "https://pudhari.news/static/img/logo.png?v=1",
        "MCLatur (Govt)": "https://mclatur.org/images/logo.png",
        "Latur Samachar": "https://www.latursamachar.com/assets/images/logo.png",
        "Dainik Ekmat": "https://epaper.dainikekmat.com/assets/images/logo.png",
        "Punyanagari E-Paper": "https://epaper.punyanagari.in/assets/images/logo.png",
        "Divya Marathi": "https://epaper.divyamarathi.com/assets/images/logo.png",
        "Sakal": "https://static.esakal.com/assets/esakal/images/sakal-logo.svg"
    };

    async function fetchNews() {
        try {
            // Check for global variable first (File Protocol support)
            if (window.newsData) {
                allNews = window.newsData;
                renderNews(allNews);

                const now = new Date();
                lastUpdatedSpan.innerHTML = `<i class="fas fa-check-circle"></i> Updated: ${now.toLocaleTimeString()}`;
                return;
            }

            // Fallback to fetch (Server mode)
            const response = await fetch('news_data.json?t=' + new Date().getTime());
            if (!response.ok) throw new Error('Network response was not ok');

            allNews = await response.json();
            renderNews(allNews);

            const now = new Date();
            lastUpdatedSpan.innerHTML = `<i class="fas fa-check-circle"></i> Updated: ${now.toLocaleTimeString()}`;

        } catch (error) {
            console.error('Error fetching news:', error);
            newsGrid.innerHTML = `
                <div class="error-msg" style="text-align:center; grid-column: 1/-1;">
                    <i class="fas fa-exclamation-triangle"></i> 
                    <h3>Failed to load news.</h3>
                    <p>Ensure the Python aggregator is running.</p>
                    <small>If opening locally, wait for aggregator to create news_data.js</small>
                </div>`;
        }
    }

    function renderNews(newsItems) {
        newsGrid.innerHTML = '';

        if (newsItems.length === 0) {
            newsGrid.innerHTML = '<p style="grid-column: 1/-1; text-align:center;">No news found recently.</p>';
            return;
        }

        newsItems.forEach(item => {
            const card = document.createElement('div');
            card.className = 'news-card';

            let imageHtml = '';

            // 1. Check for Virtual CLIP (Ekmat Page 3)
            if (item.clip && item.image) {
                const c = item.clip;
                // Calculate percentages for responsive cropping
                // Container Aspect Ratio (Height / Width)
                const aspectRatioPct = (c.h / c.w) * 100;
                // Image Width relative to Container Viewport Width
                const imgWidthPct = (c.full_width / c.w) * 100;
                // Position relative to Image Width (we shift left by x/full_width)
                const leftPct = (c.x / c.full_width) * 100;
                // Position relative to Image Height?? No, top is tricky if we don't know full height.
                // But wait, full_width is known. Full height is proportional.
                // Let's use simple px-based logic via percentages if possible.
                // Actually, simpler: top = -y * scale is handled by:
                // top: calc(-1 * (y / w) * 100%) if w is the container width reference.
                const topPct = (c.y / c.w) * 100;

                imageHtml = `
                    <div class="card-image clip-container" style="padding-top: ${aspectRatioPct}%; position: relative; overflow: hidden; background: #f0f0f0;">
                        <img src="${item.image}" alt="News Clip" style="
                            position: absolute;
                            top: -${topPct}%;
                            left: calc(-1 * ${leftPct}% * (${imgWidthPct} / 100)); 
                            width: ${imgWidthPct}%;
                            max-width: none;
                            height: auto;
                            display: block;
                        ">
                         <span class="source-badge">${item.source}</span>
                    </div>
                 `;
                // Note on left calc: left: -x_px. 
                // width_px = full_w * scale. 
                // We want left: -x * scale.
                // scale = 100% / w_unit = 1 / w.
                // left% = -x/w * 100%.
                // My manual calc above: left: calc(-1 * (c.x / c.w) * 100%)
                // Let's rely on that simpler math:
                const simpleLeftPct = (c.x / c.w) * 100;
                // We re-write the img tag with simpleLeftPct
                imageHtml = `
                    <div class="card-image clip-container" style="padding-top: ${aspectRatioPct}%; position: relative; overflow: hidden; background: #eee;">
                        <img src="${item.image}" alt="News Clip" style="
                            position: absolute;
                            top: -${topPct}%;
                            left: -${simpleLeftPct}%;
                            width: ${imgWidthPct}%;
                            max-width: none;
                            height: auto;
                            display: block;
                        ">
                         <span class="source-badge">${item.source}</span>
                    </div>
                 `;
            }
            // 2. Standard Image with Logo Fallback
            else {
                let imgUrl = item.image;

                // If no image or invalid relative path, use Source Logo
                if (!imgUrl || imgUrl.startsWith('/')) {
                    imgUrl = SOURCE_LOGOS[item.source] || DEFAULT_IMG;
                }

                // Make sure we fallback to the Logo on error even if we had a URL
                const fallbackUrl = SOURCE_LOGOS[item.source] || DEFAULT_IMG;

                imageHtml = `
                    <div class="card-image">
                        <img src="${imgUrl}" alt="News Image" onerror="this.src='${fallbackUrl}'">
                        <span class="source-badge">${item.source}</span>
                    </div>
                `;
            }

            card.innerHTML = `
                ${imageHtml}
                <div class="card-content">
                    <h3>${item.title}</h3>
                    <div class="card-meta">
                        <span><i class="far fa-clock"></i> ${timeAgo(item.timestamp)}</span>
                    </div>
                    <a href="${item.link}" target="_blank" class="read-more">Read Full News <i class="fas fa-arrow-right"></i></a>
                </div>
            `;
            newsGrid.appendChild(card);
        });
    }

    // Filter Logic
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const source = btn.getAttribute('data-source');
            if (source === 'all') {
                renderNews(allNews);
            } else if (source === 'Govt') {
                const filtered = allNews.filter(item => item.source.includes('MCLatur'));
                renderNews(filtered);
            } else {
                const filtered = allNews.filter(item => item.source.includes(source));
                renderNews(filtered);
            }
        });
    });

    // Initial Fetch
    fetchNews();

    // Auto-refresh frontend every 5 minutes (to pick up changes from the 30min backend loop)
    // Auto-refresh frontend every 5 minutes (Reloads page to pick up JS file changes)
    setInterval(() => window.location.reload(), 300000);
});
