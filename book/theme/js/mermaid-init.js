// Initialize mermaid for mdbook - loads from CDN and renders code blocks
(function() {
  var mermaidBlocks = document.querySelectorAll('code.language-mermaid');
  if (mermaidBlocks.length === 0) return;

  var script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js';
  script.onload = function() {
    mermaid.initialize({ startOnLoad: false, theme: 'default' });

    mermaidBlocks.forEach(function(block) {
      var container = block.parentElement;
      var div = document.createElement('div');
      div.className = 'mermaid';
      div.textContent = block.textContent;
      container.parentElement.replaceChild(div, container);
    });

    mermaid.run();
  };
  document.head.appendChild(script);
})();
