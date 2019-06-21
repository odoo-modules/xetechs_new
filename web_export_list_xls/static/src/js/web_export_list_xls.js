odoo.define('web_export_list_xls.ListViewExport', function (require) {
    "use strict";

    var core = require('web.core');
    var Sidebar = require('web.Sidebar');
    var session = require('web.session');
    var crash_manager = require('web.crash_manager');

    var QWeb = core.qweb;

    var _t = core._t;

    Sidebar.include({
        _redraw: function () {
            var self = this;
            this._super.apply(this, arguments);
            if (self.getParent().renderer.viewType === 'list') {
                session.user_has_group(
                    'web_export_list_xls.group_listview_export_user')
                    .then(function (has_group) {
                        var $exportBtn = self.$('.o_export_listview');
                        if (has_group && !$exportBtn.length) {
                            self.$el.find('.o_dropdown')
                                .parent().append(QWeb.render(
                                    'WebExportListview', {widget: self}));
                            self.$('.o_export_listview').on('click', self._onExportListview.bind(self));
                        }
                    });
            }
        },
        _onExportListview: function () {
            var view = this.getParent(),
                children = view.getChildren();
            var c = crash_manager;
            var _exportColumns = [];
            var exportColumns = [];
            var columnIndex = 0;
            var columnHeader = '';

            if (children) {
                children.every(function (child) {
                    if (child.field && child.field.type === 'one2many') {
                        view = child.viewmanager.views.list.controller;
                        return false;
                    }
                    if (child.field && child.field.type === 'many2many') {
                        view = child.list_view;
                        return false;
                    }
                    return true;
                });
            }
            
            $.each(view.renderer.columns, function () {
                if (this.tag === 'field' &&
                    (this.attrs.widget === undefined ||
                        this.attrs.widget !== 'handle')) {
                    _exportColumns.push(columnIndex);
                    columnHeader = '.o_list_view > thead > tr> ' +
                        'th:not([class*="o_list_record_selector"]):eq(' +
                        columnIndex + ')';
                    exportColumns.push(
                        view.$el.find(columnHeader)[0].textContent);
                }
                ++columnIndex;
            });
            var exportRows = [];
            $.blockUI();
            if (children) {
                view.$el.find('.o_list_view > tbody > tr.o_data_row:' +
                    'has(.o_list_record_selector input:checkbox:checked)')
                    .each(function () {
                        var $row = $(this);
                        var selectedRows = [];
                        $.each(_exportColumns, function () {
                            var $cell = $row.find(
                                'td.o_data_cell:eq('+this+')');
                            var $cellcheckbox = $cell.find(
                                '.custom-checkbox input:checkbox');
                            if ($cellcheckbox.length) {
                                selectedRows.push(
                                    $cellcheckbox.is(":checked")
                                        ? _t("True") : _t("False")
                                );
                            } else {
                                var text = $cell.text().trim();
                                var is_number =
                                    $cell.hasClass('o_list_number') &&
                                    !$cell.hasClass('o_float_time_cell');
                                if (is_number) {
                                    var db_params = _t.database.parameters;
                                    selectedRows.push(parseFloat(
                                        text.split(db_params.thousands_sep)
                                            .join("")
                                            .replace(db_params.decimal_point,
                                                ".")
                                            .replace(/[^\d.-]/g, "")
                                    ));
                                } else {
                                    selectedRows.push(text);
                                }
                            }
                        });
                        exportRows.push(selectedRows);
                    });
            }
            session.get_file({
                url: '/web/export/xls_view',
                data: {
                    data: JSON.stringify({
                        model: view.modelName,
                        headers: exportColumns,
                        rows: exportRows,
                    }),
                },
                complete: $.unblockUI,
                error: c.rpc_error.bind(c),
            });
        },

    });
});
