// Copyright (c) 2024, FastWork and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sfc Integration Log", {
	refresh(frm) {
        //Chỉ áp dụng với các event gọi request qua fw
        if ( frm.doc.status=='Error'){
			frm.add_custom_button('Retry', function() {
                console.log("retry");
				frappe.call({
					method:"mbw_sfc_integrations.mbw_sfc_integrations.doctype.sfc_integration_log.sfc_integration_log.resync",
					args:{
						method:frm.doc.method,
						name: frm.doc.name,
						request_data: frm.doc.request_data
					},
					callback: function(r){
						frappe.msgprint(__("Reattempting to sync"))
					}
				})
			}).addClass('btn-primary');
		}
	},
});