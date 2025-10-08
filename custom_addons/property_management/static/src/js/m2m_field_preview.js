/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Many2ManyBinaryField, many2ManyBinaryField } from "@web/views/fields/many2many_binary/many2many_binary_field";
import { useService } from "@web/core/utils/hooks";
import { FileInput } from "@web/core/file_input/file_input";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, xml } from "@odoo/owl";

const style = document.createElement('style');
style.textContent = `
    .imagem2m-preview-dialog {
        text-align: center;
    }
    .imagem2m-preview-dialog img {
        max-width: 100%;
        max-height: 80vh;
        object-fit: contain;
    }
`;
document.head.appendChild(style);

class M2MImagePreviewDialog extends Component {
    static template = xml`
        <Dialog title="props.imageName">
            <p><t t-esc="props.pre_repair_date_and_time"/></p>
            <div class="imagem2m-preview-dialog">
                <img t-att-src="props.imageUrl" alt="Image Preview"/>
            </div>
            <t t-set-slot="footer">
                <button class="btn btn-primary" t-on-click="() => props.close()">Close</button>
            </t>
        </Dialog>
    `;
    static components = { Dialog };
    static props = ["close", "imageUrl", "pre_repair_date_and_time","imageName"];
}

class Many2ManyBinaryPreviewField extends Many2ManyBinaryField {
    static template = "web.Many2ManyBinaryPreviewField";
    static components = { ...Many2ManyBinaryField.components, FileInput, M2MImagePreviewDialog };
    setup() {
        super.setup();
        this.dialogService = useService("dialog");
    }
    
    async openPreview(file) {
        const fileUrl = this.getUrl(file.id);
        const record = await this.orm.call("ir.attachment", "search_read", [
            [['id', '=', file.id]],
            ["name", "create_date", "res_id"]
        ]);

        let creation_date = record[0].create_date;
        const utcDate = new Date(creation_date);
        utcDate.setHours(utcDate.getHours() + 5);
        utcDate.setMinutes(utcDate.getMinutes() + 30);
        const options = {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true, 
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        };
        let imageName = '';
        imageName = file.name;
        creation_date = utcDate.toLocaleString('en-us',options);
        if (this.isImage(file)) {
            this.dialogService.add(M2MImagePreviewDialog, {
                imageUrl: fileUrl,
                pre_repair_date_and_time: creation_date,
                imageName: imageName,
                close: () => {} 
            });
        } else {
            window.open(fileUrl, '_blank');
        }
    }
    
    isImage(file) {
        return file.mimetype && file.mimetype.startsWith('image/');
    }

    onFileClicked(file, ev) {
        ev.preventDefault();
        this.openPreview(file);
    }

    getUrl(id) {
        return `/web/content/${id}`;
    }
    
    downloadFile(file) {
        const url = this.getUrl(file.id);
        const link = document.createElement('a');
        link.href = url;
        link.download = file.name;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

export const many2manybinarypreviewfield = {
    ...many2ManyBinaryField,
    component: Many2ManyBinaryPreviewField,
};

registry.category("fields").add("many2many_binary_preview", many2manybinarypreviewfield);
