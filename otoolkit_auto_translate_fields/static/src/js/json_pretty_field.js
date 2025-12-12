/** @odoo-module **/

import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class JsonPrettyField extends Component {
    static template = xml`
        <p style="white-space: pre-wrap; background: #f5f5f5; padding: 12px; border-radius: 6px;">
            <t t-esc="this.prettyJson"/>
        </p>
    `;
    static props = standardFieldProps;

    get prettyJson() {
        try {
            const value = this.props.record.data[this.props.name];
            return JSON.stringify(value ?? {}, null, 4);
        } catch (e) {
            return "Invalid JSON";
        }
    }
}

registry.category("fields").add("json_pretty", { component: JsonPrettyField });
