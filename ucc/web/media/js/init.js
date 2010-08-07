
// init ucc global object, all js code is namespaced into this object

var ucc = {};

(function ($) {
	
	// handle resize window event
	
	function resize() {
		$('#package-tree').height($(window).height() - 26 - 38 - 10);
		$('#word').height($(window).height() - 26 - 38);
	}
	$(resize);
	$(window).resize(resize);
	
	// load in major gui components
	
	$.include('/js/tree.js');
	$.include('/js/menu.js');
	$.include('/js/words.js');
})(jQuery);
