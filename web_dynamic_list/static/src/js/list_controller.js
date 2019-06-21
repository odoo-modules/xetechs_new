odoo.define('web_dynamic_list.ListController', function (require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
var framework = require('web.framework');
var crash_manager = require('web.crash_manager');
var field_registry = require('web.field_registry');
var ListController = require('web.ListController');
var DynamicList = require('web_dynamic_list.DynamicList');

var _t = core._t;
var QWeb = core.qweb;

ListController.include({
    custom_events: _.extend({}, ListController.prototype.custom_events, {
        update_fields: '_updateFields',
    }),
    init: function (parent, model, renderer, params) {
        var self = this;
        this._super.apply(this, arguments);
        this.uid = session.uid;
        this.view_id = params.view_id;
     },
    _checkGroup: function(){
        var self = this;
        return this.getSession().user_has_group('web_dynamic_list.group_dynamic_listview_user').then(function(has_group) {
            if(has_group){
                return self._getDefaultColumns().then(function(col_list){
                    return has_group;
                })
            }else{
                return has_group;
            }
        });
    },
    willStart: function () {
        var self = this;
        var def = this._checkGroup().then(function(has_group){
            self.has_group = has_group;
             return self.getSession().user_has_group('web_dynamic_list.group_edit_dynamic_listview_user').then(function(has_edit_group) {
                self.has_edit_group = has_edit_group;
                return has_edit_group;
            })
        })
        return $.when(this._super.apply(this, arguments), def);
    },
    renderButtons: function ($node) {
        this._super.apply(this, arguments);
        if(this.has_edit_group){
            this.$mode_switch = $(QWeb.render('ListView.switch'));
            this.$mode_switch.on('click', '.project-feature-toggle', this._onSwitchMode.bind(this));
            this.$mode_switch.find('input[type="checkbox"]').prop('checked', !!this.editable);
        }
        if (this.$buttons) {
            this.$buttons.find('.o_list_button_switch').html(this.$mode_switch);
            this.$buttons.on('click', '.o_list_button_export', this._onExportView.bind(this));  
        }
    },
    _getDefaultColumns: function(){
        var self = this;
        return this._rpc({
            model: 'ir.listview.columns',
            method: 'search_read',
            args: [[['view_id', '=', this.view_id], ['user_id', '=', self.uid]], ['list_columns']],
        }).then(function(result){
            if(result.length > 0){
                self.col_list = JSON.parse(result[0].list_columns);
            }
            return false;
        });
    },
    start: function(){
        var self = this;
        this._super.apply(this, arguments).then(function () {
            if(!self.$el.parents('.model')){
                core.bus.trigger('updatefields');
            }
        });
    },
    renderSidebar: function ($node) {
        var self = this;
        this._super.apply(this, arguments);
        if (this.has_group && !_.isUndefined($node)){
            self._renderCustomizeList($node);
        }
    },
    _renderCustomizeList: function ($node) {
        var self = this, fieldsList = [];
        var state = this.model.get(this.handle); 
        var fieldsInfo = state.fieldsInfo[this.viewType];
        var index = this.renderer.columns && _.keys(this.renderer.columns).length || 0;
        var columns = _.map(this.renderer.columns, function(rec){
            return rec.attrs.name
        });
        var fieldsList = _.map(state.fields, function(value, key){
            var val = {
                id: key,
                data: value,
                name: key,
                string: value.string,
                active: key in fieldsInfo && fieldsInfo[key].invisible == undefined,
                invisible: key in fieldsInfo && fieldsInfo[key].invisible != undefined,
            }
            if(_.contains(columns, key)){
                val = _.extend({ sequence: _.indexOf(columns, key) }, val);
            }else{
                val = _.extend({ sequence: index }, val);
                index+=1
            }
            return val;
        });
        var fieldsList = _.sortBy(fieldsList, function (o) {return o.sequence})
        var columnsList = (self.col_list)? self.col_list : _.filter(fieldsList, function(field){
            return field.active;
        });
        fieldsList = _.map(fieldsList, function(field){
            var column = _.findWhere(columnsList, {'name': field.name})
            if(column){
                return {
                    id: column.name,
                    data: field.data,
                    name: column.name,
                    string: column.string,
                    active: column.active,
                    sequence: column.sequence,
                    invisible: column.invisible,
                };
            }else{
                return field;
            }
        });
        fieldsList = _.sortBy(fieldsList, function(o) { return o.sequence;});
        this.$list_setup = new DynamicList(this, fieldsList, fieldsInfo, columnsList, this.renderer.arch.children);
        this.$list_setup.appendTo($node);
    },
    _updateFields: function (event) {
        event.stopPropagation();
        var state = this.model.get(this.handle);
        state.fieldsInfo[this.viewType] = event.data.fields;
        this.renderer.arch.children = event.data.arch;
        this.update({fieldsInfo: state.fieldsInfo}, {reload: true});
    },
    _updateButtons: function (mode) {
        this._super.apply(this, arguments);
        if(this.has_edit_group){
            this.$mode_switch.find('input[type="checkbox"]').prop('checked', !!this.editable);
        }
    },
    _onExportView: function() {
        var renderer = this.renderer;
        var record = this.model.get(this.handle);
        var fields = _.map(renderer.columns, function (field) {
            var name = field.attrs.name;
            var description = field.attrs.widget ? 
                renderer.state.fieldsInfo['list'][name].Widget.prototype.description : 
                field.attrs.string || renderer.state.fields[name].string;
            return {name: name, label: description}
        });
        var data = {
            import_compat: false,
            model: record.model,
            fields: fields,
            ids: record.res_ids || [],
            domain: record.getDomain(),
            context: record.getContext(),
        }
        framework.blockUI();
        session.get_file({
            url: '/web/export/xls',
            data: {data: JSON.stringify(data)},
            complete: framework.unblockUI,
            error: crash_manager.rpc_error.bind(crash_manager)
        });
    },
    _onSwitchMode: function(event) {
        var $el = $(event.currentTarget);
        var $input = $el.parent().find('input');
        var checked = $input.prop('checked'); 
        $input.prop('checked', !checked)
        $(event.currentTarget).toggleClass('is-checked');
        $(event.currentTarget).find('i').toggleClass('fa-check fa-times')
        if(!checked) {
            this.editable = 'top';
            this.renderer.editable = this.editable;
        } else {
            this.editable = false;
            this.renderer.editable = false;
        }
        this.update({}, {reload: true}).then(this._updateButtons.bind(this, 'readonly'));
    }

 });

});
