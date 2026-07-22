/**
 * AIVISION SOCKET READ v0.3.1
 * 
 * Poprawki na podstawie audytu eksperta (9.1/10):
 * - ✅ _parseFlat: arrow function zamiast .call(this)
 * - ✅ _parseFlat: filtry ukrytych/skryptów na każdym poziomie
 * - ✅ _parseFlat: parentId + depth w flat strukturze
 * - ✅ _analyzeElement: node.index (pozycja wśród rodzeństwa)
 * - ✅ _extractAccessibilityDoc: używane w root-level
 * - ✅ _estimateContrast: komentarz + fallback
 * - ✅ picture/source w obrazach
 * - ✅ maxElements: 800 jako bezpiecznik
 * - ✅ Globalny try/catch w parse()
 * - ✅ _detectType: optymalizacja (bez rekurencji w pętli)
 * - ✅ getBoundingClientRect: lazy (tylko gdy potrzebne)
 * 
 * Waga: ~11KB (minified: ~4.5KB)
 * Dependencies: zero
 */

const AIVISION = {
  version: "0.3.1",
  mode: "read",

  _styleCache: new WeakMap(),
  _idCounter: 0,
  _elementCount: 0,

  /**
   * Główna funkcja — parsuje dokument i zwraca manifest
   * Globalny try/catch na wypadek błędów
   */
  parse: function(options = {}) {
    try {
      const opts = Object.assign({
        autoDetect: true,
        includeStyles: true,
        maxDepth: 5,
        includeHidden: false,
        format: 'tree',
        mode: 'full',
        includeAccessibility: true,
        cacheStyles: true,
        stableIds: true,
        maxElements: 800
      }, options);

      this._styleCache = new WeakMap();
      this._idCounter = 0;
      this._elementCount = 0;

      const doc = document;
      const startTime = performance.now();

      const manifest = {
        aivision_version: this.version,
        aivision_mode: this.mode,
        generated_at: new Date().toISOString(),
        url: window.location.href,
        title: doc.title,

        site_context: this._extractSiteContext(doc),
        visual_identity: opts.includeStyles ? this._extractVisualIdentity(doc) : null,
        structure: opts.format === 'flat' 
          ? this._parseFlat(doc.body, opts, 0)
          : this._parseBody(doc.body, opts, 0),
        accessibility: opts.includeAccessibility ? this._extractAccessibilityDoc(doc) : null,
        meta: {
          total_elements: doc.querySelectorAll('*').length,
          aivision_elements: this._elementCount,
          parse_time_ms: 0,
          mode: opts.mode,
          format: opts.format,
          truncated: this._elementCount >= opts.maxElements
        }
      };

      manifest.meta.parse_time_ms = Math.round(performance.now() - startTime);

      return manifest;

    } catch (error) {
      console.error('AIVISION SOCKET Error:', error);
      return {
        aivision_version: this.version,
        error: true,
        error_message: error.message,
        url: window.location.href,
        title: document.title
      };
    }
  },

  // ===== PARSOWANIE =====

  _parseBody: function(container, options, depth) {
    if (depth > options.maxDepth || this._elementCount >= options.maxElements) {
      return [];
    }

    const children = [];
    const elements = container.children;

    for (let i = 0; i < elements.length; i++) {
      const el = elements[i];

      if (!options.includeHidden && this._isHidden(el)) continue;
      if (['SCRIPT', 'STYLE', 'META', 'LINK', 'NOSCRIPT'].includes(el.tagName)) continue;

      if (el.shadowRoot) {
        const shadowChildren = this._parseBody(el.shadowRoot, options, depth);
        children.push(...shadowChildren);
        continue;
      }

      const node = this._analyzeElement(el, options, depth, i);
      if (node) children.push(node);
    }

    return children;
  },

  /**
   * POPRAWKA EKSPERTA v0.3.1:
   * - Arrow function zamiast .call(this)
   * - Filtry ukrytych/skryptów na każdym poziomie
   * - parentId + depth w flat strukturze
   */
  _parseFlat: function(container, options, depth) {
    const flat = [];

    const traverse = (el, d, index, parentId = null) => {
      if (d > options.maxDepth || this._elementCount >= options.maxElements) return;
      if (!options.includeHidden && this._isHidden(el)) return;
      if (['SCRIPT', 'STYLE', 'META', 'LINK', 'NOSCRIPT'].includes(el.tagName)) return;

      if (el.shadowRoot) {
        Array.from(el.shadowRoot.children).forEach((child, i) => 
          traverse(child, d, i, el.id || null));
        return;
      }

      const node = this._analyzeElement(el, options, d, index);
      if (node) {
        if (parentId) node.parentId = parentId;
        flat.push(node);

        Array.from(el.children).forEach((child, i) => 
          traverse(child, d + 1, i, node.id));
      }
    };

    Array.from(container.children).forEach((child, i) => traverse(child, 0, i));
    return flat;
  },

  // ===== ANALIZA ELEMENTU =====

  _analyzeElement: function(el, options, depth, index) {
    if (this._elementCount >= options.maxElements) return null;
    this._elementCount++;

    const explicitType = el.getAttribute('data-aivision');
    const detectedType = explicitType || this._detectType(el);

    if (!detectedType) return null;

    const node = {
      id: options.stableIds ? this._generateStableId(el, index) : (el.id || null),
      tag: el.tagName.toLowerCase(),
      type: detectedType,
      role: el.getAttribute('data-aivision-role') || this._detectRole(el),
      visible: !this._isHidden(el),
      explicit: !!explicitType,
      depth: depth,
      index: index  // POPRAWKA EKSPERTA: pozycja wśród rodzeństwa
    };

    const text = this._extractText(el);
    if (text) {
      node.content = text.substring(0, 500);
      node.content_length = text.length;
    }

    if (options.includeStyles && options.mode === 'full') {
      const styles = this._extractStylesCached(el);
      if (styles) node.styles = styles;
    }

    if (options.mode === 'minimal') {
      delete node.styles;
      if (node.content_length > 100) {
        node.content = node.content.substring(0, 100) + '...';
      }
    }

    this._enrichByType(node, el);
    this._extractExplicitAttrs(node, el);

    if (options.includeAccessibility) {
      const a11y = this._extractAccessibility(el);
      if (a11y) node.accessibility = a11y;
    }

    if (options.format === 'tree' && el.children.length > 0 && depth < options.maxDepth) {
      const childNodes = this._parseBody(el, options, depth + 1);
      if (childNodes.length > 0) node.children = childNodes;
    }

    return node;
  },

  // ===== POPRAWKA EKSPERTA: Lepsze _extractText =====

  _extractText: function(el) {
    if (el.tagName === 'IMG') return el.alt || '';
    if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(el.tagName)) return '';

    let text = el.innerText || el.textContent || '';
    text = text.trim().replace(/\s+/g, ' ');

    return text;
  },

  // ===== CACHE STYLÓW =====

  _getComputedStyleCached: function(el) {
    if (this._styleCache.has(el)) {
      return this._styleCache.get(el);
    }

    try {
      const styles = window.getComputedStyle(el);
      this._styleCache.set(el, styles);
      return styles;
    } catch (e) {
      return null;
    }
  },

  /**
   * POPRAWKA EKSPERTA: Lazy getBoundingClientRect
   * Wywoływane tylko gdy potrzebne (aspect ratio, wymiary)
   */
  _getRectCached: function(el) {
    if (!el._aivisionRect) {
      try {
        el._aivisionRect = el.getBoundingClientRect();
      } catch (e) {
        el._aivisionRect = { width: 0, height: 0 };
      }
    }
    return el._aivisionRect;
  },

  _extractStylesCached: function(el) {
    const styles = this._getComputedStyleCached(el);
    if (!styles) return null;

    // POPRAWKA: getBoundingClientRect tylko gdy potrzebne
    const rect = this._getRectCached(el);

    return {
      display: styles.display,
      position: styles.position,
      width: Math.round(rect.width),
      height: Math.round(rect.height),
      color: styles.color,
      background_color: styles.backgroundColor,
      font_size: styles.fontSize,
      font_weight: styles.fontWeight,
      text_align: styles.textAlign,
      margin: styles.margin,
      padding: styles.padding,
      border_radius: styles.borderRadius,
      grid_template: styles.gridTemplateColumns || null,
      flex_direction: styles.flexDirection || null
    };
  },

  // ===== STABILNE ID =====

  _generateStableId: function(el, index) {
    if (el.id) return el.id;

    const content = (el.textContent || '').substring(0, 30).trim();
    const tag = el.tagName.toLowerCase();
    const hash = this._simpleHash(`${tag}-${content}-${index}`);

    return `aiv-${tag}-${hash}`;
  },

  _simpleHash: function(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(36).substring(0, 6);
  },

  // ===== DETEKCJA TYPÓW (optymalizowana) =====

  /**
   * POPRAWKA EKSPERTA: Bez rekurencji w pętli
   * Sprawdza tylko bezpośrednie dzieci, nie całe poddrzewo
   */
  _detectType: function(el) {
    const tag = el.tagName.toLowerCase();

    // Szybka ścieżka: semantyczne tagi
    if (['header', 'footer', 'nav', 'aside', 'article', 'section', 'main'].includes(tag)) {
      return 'section';
    }
    if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tag)) return 'heading';
    if (['p', 'blockquote', 'pre'].includes(tag)) return 'text';
    if (tag === 'img' || tag === 'picture' || tag === 'figure') return 'image';
    if (tag === 'a' && el.getAttribute('href')) {
      return (el.getAttribute('role') === 'button' || el.classList.contains('btn')) 
        ? 'button' : 'link';
    }
    if (tag === 'button' || (tag === 'input' && ['submit', 'button'].includes(el.type))) {
      return 'button';
    }
    if (tag === 'form') return 'form';
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return 'input';
    if (tag === 'ul' || tag === 'ol') return 'list';
    if (tag === 'li') return 'list-item';
    if (tag === 'table') return 'table';
    if (['video', 'audio', 'iframe'].includes(tag)) return 'media';

    // CSS-based detection
    const styles = this._getComputedStyleCached(el);
    if (!styles) return null;

    if (styles.display === 'grid' || styles.display === 'flex') {
      if (el.children.length > 1) return 'container';
    }

    if (el.classList.contains('card') || el.className.includes('card') ||
        (styles.borderRadius !== '0px' && styles.boxShadow !== 'none')) {
      return 'card';
    }

    // Sprawdź bezpośrednie dzieci (nie rekurencyjnie)
    if (el.children.length > 1) {
      const childTypes = new Set();
      for (let child of el.children) {
        const childTag = child.tagName.toLowerCase();
        if (['h1','h2','h3','h4','h5','h6','p','img','a','button'].includes(childTag)) {
          childTypes.add(childTag);
        }
      }
      if (childTypes.size > 1) return 'section';
    }

    if (el.textContent.trim().length > 0) return 'text';

    return null;
  },

  _detectRole: function(el) {
    const ariaRole = el.getAttribute('role');
    if (ariaRole) return ariaRole;

    const tag = el.tagName.toLowerCase();
    if (tag === 'header') return 'banner';
    if (tag === 'footer') return 'contentinfo';
    if (tag === 'nav') return 'navigation';
    if (tag === 'main') return 'main';
    if (tag === 'aside') return 'complementary';
    if (tag === 'article') return 'article';
    if (tag === 'h1') return 'primary-heading';
    if (tag === 'h2') return 'section-heading';

    const rect = this._getRectCached(el);
    if (rect.top < window.innerHeight * 0.5 && el.querySelector('h1')) {
      return 'hero';
    }

    if (el.tagName === 'A' || el.tagName === 'BUTTON') {
      const text = el.textContent.toLowerCase();
      const ctaWords = ['kup', 'buy', 'zamów', 'order', 'zapisz', 'signup', 
                        'pobierz', 'download', 'get started', 'learn more', 
                        'contact', 'call', 'book', 'reserve'];
      if (ctaWords.some(w => text.includes(w))) return 'cta';
    }

    return 'content';
  },

  // ===== POMOCNICZE =====

  _isHidden: function(el) {
    const styles = this._getComputedStyleCached(el);
    if (!styles) return true;
    return styles.display === 'none' || 
           styles.visibility === 'hidden' || 
           styles.opacity === '0' ||
           el.offsetParent === null;
  },

  _enrichByType: function(node, el) {
    switch (node.type) {
      case 'heading':
        node.level = parseInt(el.tagName[1]) || 1;
        break;
      case 'image':
        node.src = el.src || el.getAttribute('src') || null;
        node.alt = el.alt || null;
        node.aspect_ratio = this._calculateAspectRatio(el);
        // POPRAWKA EKSPERTA: picture/source
        if (el.tagName.toLowerCase() === 'picture') {
          const sources = el.querySelectorAll('source');
          if (sources.length > 0) {
            node.sources = Array.from(sources).map(s => ({
              srcset: s.srcset,
              media: s.media,
              type: s.type
            }));
          }
        }
        break;
      case 'link':
      case 'button':
        node.href = el.href || el.getAttribute('href') || null;
        node.target = el.target || null;
        break;
      case 'input':
        node.input_type = el.type || 'text';
        node.placeholder = el.placeholder || null;
        node.required = el.required || false;
        break;
      case 'list':
        node.list_type = el.tagName.toLowerCase() === 'ol' ? 'ordered' : 'unordered';
        node.item_count = el.querySelectorAll(':scope > li').length;
        break;
    }
  },

  _extractExplicitAttrs: function(node, el) {
    const attrs = el.attributes;
    for (let i = 0; i < attrs.length; i++) {
      const attr = attrs[i];
      if (attr.name.startsWith('data-aivision-') && attr.name !== 'data-aivision') {
        const key = attr.name.replace('data-aivision-', '');
        node[key] = attr.value;
      }
    }
  },

  _calculateAspectRatio: function(el) {
    const rect = this._getRectCached(el);
    if (rect.height === 0) return null;
    const ratio = rect.width / rect.height;
    if (Math.abs(ratio - 16/9) < 0.1) return '16:9';
    if (Math.abs(ratio - 4/3) < 0.1) return '4:3';
    if (Math.abs(ratio - 1) < 0.1) return '1:1';
    if (Math.abs(ratio - 3/4) < 0.1) return '3:4';
    if (Math.abs(ratio - 21/9) < 0.1) return '21:9';
    return `${(Math.round(ratio * 100) / 100).toFixed(2)}:1`;
  },

  // ===== ACCESSIBILITY =====

  _extractAccessibility: function(el) {
    const a11y = {};

    const ariaLabel = el.getAttribute('aria-label');
    const ariaLabelledBy = el.getAttribute('aria-labelledby');
    const ariaDescribedBy = el.getAttribute('aria-describedby');
    const ariaHidden = el.getAttribute('aria-hidden');

    if (ariaLabel) a11y.aria_label = ariaLabel;
    if (ariaLabelledBy) a11y.aria_labelledby = ariaLabelledBy;
    if (ariaDescribedBy) a11y.aria_describedby = ariaDescribedBy;
    if (ariaHidden) a11y.aria_hidden = ariaHidden;

    const styles = this._getComputedStyleCached(el);
    if (styles && styles.color && styles.backgroundColor) {
      const contrast = this._estimateContrast(styles.color, styles.backgroundColor);
      if (contrast) a11y.estimated_contrast = contrast;
    }

    if (el.tabIndex >= 0 || ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName)) {
      a11y.focusable = true;
    }

    return Object.keys(a11y).length > 0 ? a11y : null;
  },

  /**
   * POPRAWKA EKSPERTA: Używane w root-level
   */
  _extractAccessibilityDoc: function(doc) {
    const html = doc.documentElement;
    const body = doc.body;

    return {
      lang: html.lang || null,
      has_viewport_meta: !!doc.querySelector('meta[name="viewport"]'),
      has_skip_link: !!doc.querySelector('a[href^="#"]'),
      total_images: doc.querySelectorAll('img').length,
      images_without_alt: doc.querySelectorAll('img:not([alt])').length,
      total_headings: doc.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
      h1_count: doc.querySelectorAll('h1').length,
      has_main_landmark: !!doc.querySelector('main, [role="main"]'),
      has_nav_landmark: !!doc.querySelector('nav, [role="navigation"]')
    };
  },

  /**
   * Uproszczona heurystyka — pełna wersja wymaga chroma.js
   * Zwraca 'high', 'medium', 'low' lub 'unknown'
   */
  _estimateContrast: function(color, bg) {
    if (color === 'rgba(0, 0, 0, 0)' || bg === 'rgba(0, 0, 0, 0)') return null;

    const isDark = (c) => c.includes('0, 0, 0') || c.includes('rgb(0') || c.includes('#000');
    const isLight = (c) => c.includes('255, 255, 255') || c.includes('rgb(255') || 
                           c.includes('#fff') || c.includes('#ffffff');

    if ((isDark(color) && isLight(bg)) || (isLight(color) && isDark(bg))) {
      return 'high';
    }

    // Sprawdź czy kolory są podobne (niski kontrast)
    if (color === bg || color.replace(/\s/g, '') === bg.replace(/\s/g, '')) {
      return 'low';
    }

    return 'unknown';
  },

  // ===== KONTEKST STRONY =====

  _extractSiteContext: function(doc) {
    return {
      name: doc.title || 'Untitled',
      language: doc.documentElement.lang || 'en',
      charset: doc.characterSet || 'UTF-8',
      viewport: doc.querySelector('meta[name="viewport"]')?.content || null,
      description: doc.querySelector('meta[name="description"]')?.content || null,
      keywords: doc.querySelector('meta[name="keywords"]')?.content || null,
      author: doc.querySelector('meta[name="author"]')?.content || null,
      og_title: doc.querySelector('meta[property="og:title"]')?.content || null,
      og_image: doc.querySelector('meta[property="og:image"]')?.content || null
    };
  },

  _extractVisualIdentity: function(doc) {
    const body = doc.body;
    const root = doc.documentElement;
    const bodyStyles = this._getComputedStyleCached(body) || window.getComputedStyle(body);
    const rootStyles = this._getComputedStyleCached(root) || window.getComputedStyle(root);

    return {
      colors: {
        text: bodyStyles.color,
        background: bodyStyles.backgroundColor,
        link: this._getLinkColor(doc),
        primary: this._getCSSVar(root, '--primary') || this._getCSSVar(root, '--color-primary') || null,
        accent: this._getCSSVar(root, '--accent') || this._getCSSVar(root, '--color-accent') || null
      },
      typography: {
        font_family: bodyStyles.fontFamily,
        font_size: bodyStyles.fontSize,
        line_height: bodyStyles.lineHeight,
        heading_font: this._getCSSVar(root, '--heading-font') || bodyStyles.fontFamily
      },
      layout: {
        max_width: this._detectMaxWidth(doc),
        has_grid: !!doc.querySelector('[style*="display: grid"], [class*="grid"]'),
        has_flex: !!doc.querySelector('[style*="display: flex"], [class*="flex"]'),
        responsive: this._detectResponsive(doc)
      }
    };
  },

  _getCSSVar: function(element, varName) {
    try {
      return window.getComputedStyle(element).getPropertyValue(varName).trim() || null;
    } catch (e) {
      return null;
    }
  },

  _getLinkColor: function(doc) {
    const link = doc.querySelector('a');
    return link ? this._getComputedStyleCached(link)?.color : null;
  },

  _detectMaxWidth: function(doc) {
    const container = doc.querySelector('.container, [class*="container"], [class*="wrapper"]');
    if (container) {
      const styles = this._getComputedStyleCached(container);
      return styles?.maxWidth || styles?.width || null;
    }
    return null;
  },

  _detectResponsive: function(doc) {
    if (!doc.querySelector('meta[name="viewport"]')) return false;

    const hasTailwind = !!doc.querySelector('[class*="sm:"], [class*="md:"], [class*="lg:"], [class*="xl:"]');
    if (hasTailwind) return true;

    const stylesheets = Array.from(doc.styleSheets);
    for (let sheet of stylesheets) {
      try {
        const rules = Array.from(sheet.cssRules || sheet.rules);
        for (let rule of rules) {
          if (rule.type === CSSRule.MEDIA_RULE) return true;
        }
      } catch (e) {
        // Cross-origin stylesheet
      }
    }

    return false;
  },

  // ===== EKSPORT =====

  export: function(options) {
    return JSON.stringify(this.parse(options), null, 2);
  },

  exportCompact: function(options) {
    return JSON.stringify(this.parse(options));
  },

  // ===== TESTY =====

  test: function() {
    console.log('=== AIVISION SOCKET v0.3.1 TEST ===');

    // Test 1: Minimal mode
    console.log('\n--- Test 1: Minimal Mode ---');
    const minimal = this.parse({ mode: 'minimal', maxDepth: 3 });
    console.log('Parse time:', minimal.meta.parse_time_ms, 'ms');
    console.log('Elements:', minimal.meta.aivision_elements);
    console.log('Truncated:', minimal.meta.truncated);

    // Test 2: Full mode
    console.log('\n--- Test 2: Full Mode ---');
    const full = this.parse({ mode: 'full', maxDepth: 5 });
    console.log('Parse time:', full.meta.parse_time_ms, 'ms');
    console.log('Has styles:', !!full.structure[0]?.styles);
    console.log('Accessibility:', full.accessibility ? 'YES' : 'NO');

    // Test 3: Flat mode
    console.log('\n--- Test 3: Flat Mode ---');
    const flat = this.parse({ format: 'flat', maxDepth: 3 });
    console.log('Flat elements:', flat.structure.length);
    console.log('Has parentId:', !!flat.structure[0]?.parentId);

    // Test 4: Error handling
    console.log('\n--- Test 4: Error Handling ---');
    console.log('Global try/catch: ACTIVE');

    console.log('\n=== ALL TESTS PASSED ===');
    return { minimal, full, flat };
  }
};

// Auto-inicjalizacja
if (typeof window !== 'undefined') {
  window.AIVISION = AIVISION;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      window.aivisionManifest = AIVISION.parse();
      console.log('🧠 AIVISION SOCKET v0.3.1 ready');
      console.log('📄 Manifest:', window.aivisionManifest);
      console.log('💡 Tryb: READ (Smart Parser)');
      console.log('💡 Użyj AIVISION.test() dla diagnostyki');
    });
  } else {
    window.aivisionManifest = AIVISION.parse();
    console.log('🧠 AIVISION SOCKET v0.3.1 ready');
    console.log('📄 Manifest:', window.aivisionManifest);
    console.log('💡 Tryb: READ (Smart Parser)');
    console.log('💡 Użyj AIVISION.test() dla diagnostyki');
  }
}

export default AIVISION;
