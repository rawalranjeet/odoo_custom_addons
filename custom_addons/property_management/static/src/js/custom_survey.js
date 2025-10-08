/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import "@survey/js/survey_form";   // <-- ensures SurveyFormWidget is registered

publicWidget.registry.SurveyFormWidget.include({
    /**
     * Override _onSubmit to add custom logic
     */
    _onSubmit: function (event) {
        event.preventDefault();
        const options = {};
        const target = event.currentTarget;
        const orderId = target.dataset.order_id;
        if (orderId) {
            options.orderId = parseInt(orderId);  // pass into options
        }
        if (target.value === 'previous') {
            options.previousPageId = parseInt(target.dataset['previousPageId']);
        } else if (target.value === 'next_skipped') {
            options.nextSkipped = true;
        } else if (target.value === 'finish') {
            options.isFinish = true;
        }
        this._submitForm(options);
    },
    _onNextScreenDone: function (options) {
        var self = this;
        var result = this.nextScreenResult;

        if ((!(options && options.isFinish) || result.has_skipped_questions)
            && !this.options.sessionInProgress) {
            this.preventEnterSubmit = false;
        }
        if (result && !result.error) {
            this.$(".o_survey_form_content").empty();
            this.$(".o_survey_form_content").html(result.survey_content);

            if (result.survey_progress && this.$surveyProgress.length !== 0) {
                this.$surveyProgress.html(result.survey_progress);
            } else if (options.isFinish && this.$surveyProgress.length !== 0) {
                this.$surveyProgress.remove();
            }

            if (result.survey_navigation && this.$surveyNavigation.length !== 0) {
                this.$surveyNavigation.html(result.survey_navigation);
                this.$surveyNavigation.find('.o_survey_navigation_submit').on('click', self._onSubmit.bind(self));
            }

            // Hide timer if end screen (if page_per_question in case of conditional questions)
            if (self.options.questionsLayout === 'page_per_question' && this.$('.o_survey_finished').length > 0) {
                options.isFinish = true;
            }

            // Start datetime pickers
            self.trigger_up("widgets_start_request", { $target: this.$el.find('.o_survey_form_date') });
            if (this.options.isStartScreen || (options && options.initTimer)) {
                this._initTimer();
                this.options.isStartScreen = false;
            } else {
                if (this.options.sessionInProgress && this.surveyTimerWidget) {
                    this.surveyTimerWidget.destroy();
                }
            }
            if (options && options.isFinish && !result.has_skipped_questions) {
                this._initResultWidget();
                if (this.surveyBreadcrumbWidget) {
                    this.$('.o_survey_breadcrumb_container').addClass('d-none');
                    this.surveyBreadcrumbWidget.destroy();
                }
                if (this.surveyTimerWidget) {
                    this.surveyTimerWidget.destroy();
                }
            } else {
                this._updateBreadcrumb();
            }
            self._initChoiceItems();
            self._initTextArea();

            if (this.options.sessionInProgress && this.$('.o_survey_form_content_data').data('isPageDescription')) {
                // prevent enter submit if we're on a page description (there is nothing to submit)
                this.preventEnterSubmit = true;
            }
            // Background management - reset background overlay opacity to 0.7 to discover next background.
            if (this.options.refreshBackground) {
                $('div.o_survey_background').css("background-image", "url(" + result.background_image_url + ")");
                $('div.o_survey_background').removeClass('o_survey_background_transition');
            }
            this.$('.o_survey_form_content').fadeIn(this.fadeInOutDelay);
            $("html, body").animate({ scrollTop: 0 }, this.fadeInOutDelay);

            this.$('button[type="submit"]').removeClass('disabled');

            this._scrollToFirstError();
            self._focusOnFirstInput();
            if (options.isFinish) {
                const saleOrderId = options.orderId;
                if (saleOrderId) {
                    window.location.href = `/odoo/sales/${saleOrderId}`;
                    return;
                }
            }

        } else if (result && result.fields && result.error === 'validation') {
            this.$('.o_survey_form_content').fadeIn(0);
            this._showErrors(result.fields);
        } else {
            var $errorTarget = this.$('.o_survey_error');
            $errorTarget.removeClass("d-none");
            scrollTo($errorTarget[0]);
        }
    },
});
