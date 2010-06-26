
// Load Tree Control

$(function () {
	$("#package-tree").tree({
		data: { 
			type: "json",
			opts: {
				method: "GET",
				url: '/ajax/words/get?data={}'
			}
		},
		opened: ['declaration']
	});
});
