window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    tags: 'ams',
    macros: {
    },
  },

};

(function () {
  var script = document.createElement('script');
    script.src = '/mathjax/tex-chtml-full.js'
  script.async = true;
  document.head.appendChild(script);
})();
