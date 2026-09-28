import logging
import requests
from decouple import config

logger = logging.getLogger(__name__)


def send_email(email: str, subject: str, message: str) -> bool:
    """Sends email via third-party HTTP API endpoint configured in .env."""
    base_url = config("AUTH_URL", default="").rstrip("/")

    if not base_url:
        logger.error("AUTH_URL is missing in environment settings.")
        return False

    endpoint_url = f"{base_url}/send-normal-email"

    # API Payload
    payload = {
        "email": email,
        "subject": subject,
        "message": message,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        response = requests.post(
            endpoint_url, json=payload, headers=headers, timeout=10
        )

        # Check for HTTP success status (200 OK or 201 Created)
        if response.status_code in [200, 201]:
            logger.info(f"Email successfully dispatched to {email} via API.")
            return True
        else:
            logger.error(
                f"Third-party Email API failed with status {response.status_code}: {response.text}"
            )
            return False

    except requests.exceptions.RequestException as e:
        logger.error(
            f"Failed to connect to Third-party Email API at {endpoint_url}: {str(e)}"
        )
        return False


def generate_kpi_submission_html_email(
    supervisor_name: str,
    staff_name: str,
    staff_pf: str,
    window_title: str,
    submission_date: str,
    comments: str = "",
) -> str:
    """Generates a professional HTML email template for KPI submissions."""

    # Format optional comments block
    comments_html = ""
    if comments:
        comments_html = f"""
        <div style="background-color: #f8fafc; border-left: 4px solid #0284c7; padding: 12px 16px; margin: 16px 0; border-radius: 0 6px 6px 0;">
            <p style="margin: 0; font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase;">Submission Comments:</p>
            <p style="margin: 4px 0 0 0; font-size: 14px; color: #334155; font-style: italic;">"{comments}"</p>
        </div>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KPI Submission Notification</title>
</head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 20px; -webkit-font-smoothing: antialiased;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #0f172a; padding: 24px 32px; text-align: left;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 600; letter-spacing: -0.5px;">HR Staff Portal</h1>
                        </td>
                    </tr>
                    
                    <!-- Sub-header Banner -->
                    <tr>
                        <td style="background-color: #0284c7; padding: 10px 32px; text-align: left;">
                            <span style="color: #ffffff; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Pending Approval</span>
                        </td>
                    </tr>

                    <!-- Body Content -->
                    <tr>
                        <td style="padding: 32px;">
                            <p style="margin: 0 0 16px 0; font-size: 16px; color: #1e293b; line-height: 1.5;">Dear <strong>{supervisor_name}</strong>,</p>
                            
                            <p style="margin: 0 0 24px 0; font-size: 15px; color: #475569; line-height: 1.6;">
                                Staff <strong>{staff_pf}</strong> : <strong>{staff_name}</strong> has submitted their performance appraisal for your review and formal evaluation.
                            </p>

                            <!-- Information Table -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 20px;">
                                <tr>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #64748b; font-weight: 600; width: 35%;">Staff Name:</td>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #0f172a; font-weight: 500;">{staff_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #64748b; font-weight: 600;">OPF Number:</td>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #0f172a; font-weight: 500;">{staff_pf}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #64748b; font-weight: 600;">Evaluation Title:</td>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #0284c7; font-weight: 600;">{window_title}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; font-size: 14px; color: #64748b; font-weight: 600;">Submission Date:</td>
                                    <td style="padding: 12px 16px; font-size: 14px; color: #0f172a; font-weight: 500;">{submission_date}</td>
                                </tr>
                            </table>

                            {comments_html}

                            <p style="margin: 20px 0 24px 0; font-size: 14px; color: #475569; line-height: 1.5;">
                                Please log into the HR Staff portal to review the performance targets, actual achievements, and record your supervisory scores.
                            </p>

                            <!-- Footer Note -->
                            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                            <p style="margin: 0; font-size: 12px; color: #94a3b8; text-align: center;">
                                This is an automated system notification from the HR Performance Management Module. Please do not reply directly to this email.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""


def generate_hr_kpi_approval_html_email(
    supervisor_name: str,
    staff_name: str,
    staff_pf: str,
    window_title: str,
    approval_date: str,
    comments: str,
    total_score: str,
) -> str:
    """Generates a styled HTML email for HR upon KPI approval."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KPI Appraisal Approved</title>
</head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 20px; -webkit-font-smoothing: antialiased;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #0f172a; padding: 24px 32px;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 600;">HR Management System</h1>
                        </td>
                    </tr>
                    
                    <!-- Banner -->
                    <tr>
                        <td style="background-color: #16a34a; padding: 10px 32px;">
                            <span style="color: #ffffff; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Appraisal Approved</span>
                        </td>
                    </tr>

                    <!-- Body Content -->
                    <tr>
                        <td style="padding: 32px;">
                            <p style="margin: 0 0 16px 0; font-size: 16px; color: #1e293b;">Dear <strong>HR Team</strong>,</p>
                            
                            <p style="margin: 0 0 24px 0; font-size: 15px; color: #475569; line-height: 1.6;">
                                The KPI appraisal for <strong>{staff_name}</strong> has been officially reviewed and approved by supervisor <strong>{supervisor_name}</strong>.
                            </p>

                            <!-- Information Table -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 20px;">
                                <tr>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #64748b; font-weight: 600; width: 35%;">Staff Name:</td>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #0f172a; font-weight: 500;">{staff_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #64748b; font-weight: 600;">OPF Number:</td>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #0f172a; font-weight: 500;">{staff_pf}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #64748b; font-weight: 600;">Evaluation Title:</td>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #0284c7; font-weight: 600;">{window_title}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #64748b; font-weight: 600;">Final Total Score:</td>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #16a34a; font-weight: 700;">{total_score}%</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; font-size: 14px; color: #64748b; font-weight: 600;">Approved Date:</td>
                                    <td style="padding: 12px 16px; font-size: 14px; color: #0f172a; font-weight: 500;">{approval_date}</td>
                                </tr>
                            </table>

                            <!-- Comments Section -->
                            <div style="background-color: #f0fdf4; border-left: 4px solid #16a34a; padding: 12px 16px; margin: 16px 0; border-radius: 0 6px 6px 0;">
                                <p style="margin: 0; font-size: 13px; color: #166534; font-weight: 600; text-transform: uppercase;">Supervisor Remarks:</p>
                                <p style="margin: 4px 0 0 0; font-size: 14px; color: #14532d; font-style: italic;">"{comments}"</p>
                            </div>

                            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                            <p style="margin: 0; font-size: 12px; color: #94a3b8; text-align: center;">
                                This is an automated system notification from the HRMS Staff Portal.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""


def generate_staff_kpi_rejection_html_email(
    staff_name: str,
    supervisor_name: str,
    window_title: str,
    rejection_date: str,
    comments: str,
) -> str:
    """Generates a styled HTML email notifying staff that their KPI appraisal was returned for corrections."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KPI Appraisal Returned for Corrections</title>
</head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 20px; -webkit-font-smoothing: antialiased;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #0f172a; padding: 24px 32px;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 600;">HRMS Staff Portal</h1>
                        </td>
                    </tr>
                    
                    <!-- Banner -->
                    <tr>
                        <td style="background-color: #dc2626; padding: 10px 32px;">
                            <span style="color: #ffffff; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Action Required: Returned for Corrections</span>
                        </td>
                    </tr>

                    <!-- Body Content -->
                    <tr>
                        <td style="padding: 32px;">
                            <p style="margin: 0 0 16px 0; font-size: 16px; color: #1e293b;">Dear <strong>{staff_name}</strong>,</p>
                            
                            <p style="margin: 0 0 24px 0; font-size: 15px; color: #475569; line-height: 1.6;">
                                Your KPI appraisal for <strong>{window_title}</strong> has been reviewed by your supervisor, <strong>{supervisor_name}</strong>, and returned to you for necessary corrections or revisions.
                            </p>

                            <!-- Information Table -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 20px;">
                                <tr>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #64748b; font-weight: 600; width: 35%;">Evaluation Period:</td>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #0284c7; font-weight: 600;">{window_title}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #64748b; font-weight: 600;">Reviewed By:</td>
                                    <td style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #0f172a; font-weight: 500;">{supervisor_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; font-size: 14px; color: #64748b; font-weight: 600;">Returned Date:</td>
                                    <td style="padding: 12px 16px; font-size: 14px; color: #0f172a; font-weight: 500;">{rejection_date}</td>
                                </tr>
                            </table>

                            <!-- Rejection Feedback Comments -->
                            <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 12px 16px; margin: 16px 0; border-radius: 0 6px 6px 0;">
                                <p style="margin: 0; font-size: 13px; color: #991b1b; font-weight: 600; text-transform: uppercase;">Supervisor Feedback / Required Changes:</p>
                                <p style="margin: 4px 0 0 0; font-size: 14px; color: #7f1d1d; font-style: italic;">"{comments}"</p>
                            </div>

                            <p style="margin: 20px 0 24px 0; font-size: 14px; color: #475569; line-height: 1.5;">
                                Please log into the HRMS Staff Portal, address the feedback above, update your performance ratings/targets, and resubmit your appraisal for review.
                            </p>

                            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">
                            <p style="margin: 0; font-size: 12px; color: #94a3b8; text-align: center;">
                                This is an automated system notification from the HRMS Staff Portal. Please do not reply directly to this email.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
