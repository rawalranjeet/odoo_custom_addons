/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { onMounted } from "@odoo/owl";

patch(KanbanRenderer.prototype, {
    setup() {
        super.setup();

        onMounted(() => {
            const modelName = this.props.list.resModel;
            const container = document.querySelector(".o_control_panel_main_buttons");
            if (!container) {
                return;
            }

            // Remove previous custom elements
            container.querySelectorAll(".custom-room-line, .custom-property-name, .custom-component-name").forEach(el => el.remove());

            const createH6 = (val, className) => {
                const h6 = document.createElement("h6");
                h6.classList.add(className, "m-0", "me-2", "fw-bold"); // Styling classes
                h6.textContent = val;
                container.appendChild(h6);
            };

            if (modelName === "property.component.component") {
                const roomLineIds = this.props.list.records
                    .map(r => r.data?.room_line_char)
                    .filter(Boolean);

                [...new Set(roomLineIds)].forEach(val => createH6(val, "custom-room-line"));

            } else if (modelName === "property.room.room") {
                const propertyNames = this.props.list.records
                    .map(r => r.data?.property_name_char)
                    .filter(Boolean);

                [...new Set(propertyNames)].forEach(val => createH6(val, "custom-property-name"));

            } else if (modelName === "property.preparation") {
                const componentNames = this.props.list.records
                    .map(r => r.data?.component_name_char)
                    .filter(Boolean);

                [...new Set(componentNames)].forEach(val => createH6(val, "custom-component-name"));
            }
        });
    },
});




///** @odoo-module **/
//
//import { patch } from "@web/core/utils/patch";
//import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
//import { onMounted } from "@odoo/owl";
//
//patch(KanbanRenderer.prototype, {
//    setup() {
//        super.setup();
//
//        onMounted(() => {
//            const modelName = this.props.list.resModel;
//            const container = document.querySelector(".o_control_panel_main_buttons");
//            if (!container) {
//                return;
//            }
//
//            container.querySelectorAll(".custom-room-line, .custom-property-name, .custom-component-name").forEach(el => el.remove());
//
//            if (modelName === "property.component.component") {
//                const roomLineIds = this.props.list.records
//                    .map(r => r.data?.room_line_char)
//                    .filter(Boolean);
//
//                const uniqueRoomLineIds = [...new Set(roomLineIds)];
//
//                uniqueRoomLineIds.forEach(val => {
//                    const button = document.createElement("button");
//                    button.classList.add("btn", "btn-primary", "custom-room-line");
//                    button.innerHTML = `<strong>${val}</strong>`;
//                    button.addEventListener("click", () => {
//                        console.log("Clicked Room:", val);
//                    });
//                    container.appendChild(button);
//                });
//            } else if (modelName === "property.room.room") {
//                const propertyNames = this.props.list.records
//                    .map(r => r.data?.property_name_char)
//                    .filter(Boolean);
//
//                const uniquePropertyNames = [...new Set(propertyNames)];
//
//                uniquePropertyNames.forEach(val => {
//                    const button = document.createElement("button");
//                    button.classList.add("btn", "btn-primary", "custom-property-name");
//                    button.innerHTML = `<strong>${val}</strong>`;
//                    button.addEventListener("click", () => {
//                        console.log("Clicked Property:", val);
//                    });
//                    container.appendChild(button);
//                });
//            } else if (modelName === "property.preparation") {
//                const componentNames = this.props.list.records
//                    .map(r => r.data?.component_name_char)
//                    .filter(Boolean);
//
//                const uniqueComponentNames = [...new Set(componentNames)];
//
//                uniqueComponentNames.forEach(val => {
//                    const button = document.createElement("button");
//                    button.classList.add("btn", "btn-primary", "custom-component-name");
//                    button.innerHTML = `<strong>${val}</strong>`;
//                    button.addEventListener("click", () => {
//                        console.log("Clicked Component:", val);
//                    });
//                    container.appendChild(button);
//                });
//            }
//        });
//    },
//});
