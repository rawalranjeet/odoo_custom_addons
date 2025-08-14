/** @odoo-module **/
import {patch} from "@web/core/utils/patch";
import {many2OneField} from "@web/views/fields/many2one/many2one_field";
import { rpc } from "@web/core/network/rpc";
import { Component, useState , onMounted} from "@odoo/owl";
import { session } from "@web/session";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";

import { registry } from "@web/core/registry";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { useService } from "@web/core/utils/hooks";



patch(many2OneField, {
    

    extractProps({ attrs, context, decorations, options, string }, dynamicInfo) {
        var res = super.extractProps({ attrs, context, decorations, options, string }, dynamicInfo) 
        
        // const config = rpc("/web/dataset/call_kw/", {
        //     model: "ir.config_parameter",
        //     method: "get_param",
        //     args: ['many2one_config.enable_edit_many2one'],
        //     kwargs: {},
        // });
        
        // config.then((result)=> console.log("await"))

        // console.log("result1")

        if (session.disable_edit_many2one){
                res.canQuickCreate = false;
                res.canCreateEdit = false;
                res.canCreate = false;
                res.canWrite = false;
               
            }
       
        return res
    },


   
});


export class MyKanbanController extends KanbanController {
    static template = 'many2one_config.kanban_sidebar_template'

    setup() {
        super.setup();

        this.name = useState({value:''})
    }

   

}


registry.category("views").add("kanban_sidebar", {
    ...kanbanView,
    Controller: MyKanbanController,
});