/** @odoo-module **/

import { dataUrlToBlob } from "@mail/core/common/attachment_uploader_hook";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useX2ManyCrud } from "@web/views/fields/relational_utils";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { FileUploader } from "@web/views/fields/file_handler";
import { Component } from "@odoo/owl";

export class KanbanAttachmentUploader extends Component {
    static template = "property.KanbanAttachmentUploader";
    static components = { FileUploader };
    static props = { ...standardFieldProps };

    setup() {
//        debugger
        this.mailStore = useService("mail.store");
        this.attachmentUploadService = useService("mail.attachment_upload");
        this.operations = useX2ManyCrud(() => this.props.record.data["attachment_ids"], true);
    }

    // Works for single or multiple files
    // In your KanbanAttachmentUploader component
    async onFileUploaded(payload) {

        const items = Array.isArray(payload) ? payload : [payload];
//        const resModel = 'property.room.line';
        if (this.props.record && this.props.record.data)
        {
            let resModel = null;
            let resId = null
//            debugger
            if (this.props.record._config.resModel == 'property.room.room'){
                resModel = 'property.room.line';
                if(this.props.record.data.property_id && this.props.record.data.property_id.length > 1){
                    resId = this.props.record.data.property_id[0]
                }
            }
            if (this.props.record._config.resModel == 'property.preparation'){
                resModel = 'property.com.preparation.line';
                if(this.props.record.data.com_preparation_line_id && this.props.record.data.com_preparation_line_id.length > 1){
                    resId = this.props.record.data.com_preparation_line_id[0]
                }
            }
            // First, ensure your model inherits from mail.thread in Python.
        // Then, create the thread object here.
            const thread = await this.mailStore.Thread.insert({
                model: resModel,
                id: resId,
            });
            for (const item of items) {
                const { data, name, type } = item;
                const file = new File([dataUrlToBlob(data, type)], name, { type });

                // Call the upload method directly with the thread and null for the composer.
                const attachment = await this.attachmentUploadService.upload(thread, null, file);

                // This line is crucial to save the attachment ID to the record.
                await this.operations.saveRecord([attachment.id]);
            }
        }



    }
}

registry.category("fields").add("kanban_attachment_uploader", { component: KanbanAttachmentUploader });
