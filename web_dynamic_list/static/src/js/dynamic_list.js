odoo.define('web_dynamic_list.DynamicList', function(require) {
    "use strict";

    var core = require('web.core');
    var ListView = require('web.ListView');
    var ListController = require('web.ListController');
    var session = require('web.session');
    var field_registry = require('web.field_registry');
	var Widget = require('web.Widget');
    var QWeb = core.qweb;

    var _t = core._t;

    ListView.include({
		init: function (viewInfo, params) {
            this._super.apply(this, arguments);
            this.controllerParams.view_id = viewInfo.view_id;
        },
	});
	var DynamicList = Widget.extend({
	    template: 'ListView.columns',
	    events: {
	        'click .btn-toggle': '_onColumnToggle',
            'click .th_ul li': '_onDropdownToggle',
            'keyup #col-search': '_onSearchField',
            'click #restore_default': '_onRestoreDefault',
	    },
	    init: function (parent, fields, info, col_list, arch) {
	    	var self = this;
	    	this._super.apply(this, arguments);
	        this.info = $.extend(true, {}, info);
	        this.fields = fields;
	        this.view_id = parent.view_id;
	        this.uid = parent.uid;
            this.arch = _.object(_.map(_.extend({}, arch), function(value) {
                return [value.attrs.name, value] 
            }));
	        this.col_list = col_list || [];
	    },
        start: function(){
         	var self = this;
            return this._super.apply(this, arguments).then(function(){
                self.$el.find('.th_ul .o_item').each(function(){
                    $(this).attr('data-search-term', $(this).find('#o-column_name').text().toLowerCase());
                });
                self._onColumnSort();
                _.delay(function () {
                    self._fieldsUpdate()
                }, 100);
                core.bus.on('updatefields', self, self._fieldsUpdate);
            })
		},
	    _onColumnToggle: function (ev) {
	    	var self = this, $el = $(ev.currentTarget);
	    	var $input = $el.parents('.column-switch').find('input');
	    	$el.toggleClass('is-checked');
	    	$el.find('i').toggleClass('fa-check fa-times')
	    	var checked = $input.prop('checked'); 
	    	$input.prop('checked', !checked)
            var field = _.findWhere(self.col_list, {
                name: $input.attr('name')
            });
            var column = _.findWhere(self.fields, {
                name: $input.attr('name')
            });
            if(_.isUndefined(field)){ 
                self.col_list.push({
                    'name':$input.attr('name'),
                    'active':!checked,
                    'sequence':$input.data('seq'),
                    'string': column.string,
                    'invisible': column.invisible,
                    'data': column.data
                })
            }else{
                field.active = !field.active;
            }
            column.active = !column.active; 
            this._fieldsUpdate();
	    	this._setCurrentState();
	  	},
        _onDropdownToggle: function(ev){
            ev.stopPropagation();
        },  
        _onSearchField: function(ev){
            var self = this, $el = $(ev.currentTarget);
            this.$el.find('.th_ul .o_item').each(function(){
                var searchTerm = $el.val().toLowerCase();
                if ($(this).filter('[data-search-term *= ' + searchTerm + ']').length > 0 || searchTerm.length < 1) {
                    $(this).show();
                } else {
                    $(this).hide();
                }
            });
        },
        _onColumnSort: function(){
            var self = this;
            self.$el.find('.th_ul').sortable({
                cancel: ".no-sort",
                placeholder: "ui-state-highlight",
                axis: "y",
                items: "li:not(.no-sort)",
                update: self._onFieldMove.bind(self),
            });
        },
        _onFieldMove: function(ev, ui) {
            var self = this,keys = {};
            _.each(ev.target.children, function (element, sequence) {
                var $element = $(element);
                if ($element.hasClass("list-group-item")) {
                    keys[$element.data('id')] = sequence;
                }
            });
            this.fields = _.sortBy(this.fields, function(field) { 
                return keys[field.id];
            });
            this.col_list = _.sortBy(this.col_list, function(field) { 
                return keys[field.name];
            });
            self.fields = _.map(this.fields, function(field, sequence) {
                field.sequence = sequence;
                return field;
            });
            self.col_list = _.map(this.col_list, function(field, sequence) {
                field.sequence = sequence;
                return field;
            });
            this._fieldsUpdate();
            self._setCurrentState();
        },
        _onRestoreDefault: function(){
            var self = this;
            self._getColumns(self.view_id, self.uid).then(function(result){
                if(result.length){
                    self._rpc({
                        model: 'ir.listview.columns',
                        method: 'unlink',
                        args: result,
                    }).then(function(e){
                        location.reload();
                    })
                }
            })
        },
        _fieldsUpdate: function(){
            this.trigger_up('update_fields', {
                arch: this._getArch(),
                fields: this._getFieldInfo(),
            });
        },
	  	_setColumns: function(results, columns){
	  		var self = this;
			if(results.length === 1){
		  		self._rpc({
					model: 'ir.listview.columns',
					method: 'write',
					args: [results, {'list_columns': columns}],
				});
    		}else{
				self._rpc({
					model: 'ir.listview.columns',
					method: 'create',
					args: [{
						'view_id': self.view_id,
						'list_columns': columns,
						'user_id': self.uid
					}],
				})
    		}
	  	},
	  	_getColumns: function(view_id, uid){
	  		return this._rpc({
                model: 'ir.listview.columns',
                method: 'search',
                args: [[["view_id", "=", view_id],["user_id", "=", uid]]],
            });
	  	},
	  	_setCurrentState: function(){
			var self=this, cols=[];
			_.each(self.col_list, function (c) {
                var cannedResponse = _.omit(c, 'id', 'data')
                cols.push(cannedResponse);
            });
            self._getColumns(self.view_id, self.uid).then(function(results){
				self._setColumns(results, JSON.stringify(cols))
			})
		},
	  	_getArch: function () {
        	var arch = [];
        	_.each(this.fields, function (field) {
        		if (field.active && field.name in this.arch) {
        			arch.push(this.arch[field.name]);
        		} else if (field.active && !(field.name in this.arch)) {
        			arch.push({
        				attrs: {
        					modifiers: {
        						readonly: field.data.readonly,
                				required: field.data.required,
        					},
        					name: field.name,
        				},
    	    			children: [],
    	    			tag: "field",
        			});
        		}
        	}, this);
        	return arch;
        },
	  	_getFieldInfo: function () {
        	var info = {};
        	_.each(this.fields, function (field) {
        		if (field.name in this.info) {
                    info[field.name] = $.extend(true, {}, this.info[field.name]);
        			info[field.name].modifiers = _.extend({}, info[field.name].modifiers, {
        				column_invisible: !field.active,
        			});
        			info[field.name].invisible = !field.active;
        		} else if (field.active && !(field.name in this.info)) {
                    var type = field.data.type;
                    var attrs = {
                        Widget: field_registry.getAny(["list." + type, type, "abstract"]),
                        modifiers: {
                            readonly: field.data.readonly,
                            required: field.data.required,
                        },
                        name: field.name,
                        invisible: !field.active
                    };
                    if (type === 'one2many' || type === 'many2many') {
                        if (attrs.Widget.prototype.useSubview) {
                        	attrs.views = {};
                        }
                        if (attrs.Widget.prototype.fieldsToFetch) {
                            attrs.viewType = 'default';
                            attrs.relatedFields = _.extend({}, attrs.Widget.prototype.fieldsToFetch);
                            attrs.fieldsInfo = {
                                'default': _.mapObject(attrs.Widget.prototype.fieldsToFetch, function () {
                                    return {};
                                }),
                            };
                        } 
                        if (attrs.Widget.prototype.fieldDependencies) {
                            attrs.fieldDependencies = attrs.Widget.prototype.fieldDependencies;
                        }
                    }
        			info[field.name] = attrs;
        		}
        	}, this);
        	return info;
        },
	});

	return DynamicList;

});