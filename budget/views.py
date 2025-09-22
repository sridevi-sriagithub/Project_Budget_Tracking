from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED,HTTP_400_BAD_REQUEST
from rest_framework import status
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from project_creation.models import Project
from django.shortcuts import get_object_or_404
from .models import ProjectEstimation, ProjectPaymentTracking, ProjectPaymentMilestone, PaymentTransaction, AdditionalBudgetRequest, Notification, Rule, PaymentHistory, AuditLog, Hold, ChangeRequest,Invoice
from .serializers import (
    ProjectPaymentTrackingSerializer, ProjectPaymentMilestoneSerializer,EstimationSerializer,
    PaymentTransactionSerializer, AdditionalBudgetRequestSerializer, NotificationSerializer, RuleSerializer,ProjectPaymentTrackingUpdateSerializer, HoldSerializer, ProfitLossSerializer,ChangeRequestSerializer
    ,InvoiceSerializer
)
from .services import (
    create_milestone,create_transaction,request_additional, approve_request,
    reject_request,evaluate_and_notify,create_payment, update_payment, get_payment,notify_budget_request,
    validate_payment_against_policy,calculate_project_profit_loss, notify_milestone_update,BudgetMonitorService,notify_budget_breach )
from .permission import IsFinanceApprover
from django.utils import timezone
import traceback
from decimal import Decimal
from django.db import models
from .tasks import recalculate_project_finances, send_budget_alerts
from django.forms.models import model_to_dict
from django.utils.timezone import now
from django.conf import settings
from datetime import timedelta
import uuid, os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import FileResponse, Http404

    
class EstimationCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    
    
    def post(self, request):
        try:
            serializer = EstimationSerializer(data=request.data)
            if serializer.is_valid():
                estimation = serializer.save()
                print("New Estimation Created:", model_to_dict(estimation))
                
                # Trigger background tasks asynchronously
                recalculate_project_finances.delay(estimation.project.id)
                send_budget_alerts.delay(estimation.project.id)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("Error in POST:", e)
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   
    def get(self, request, pk=None):
        if pk:
            estimation = get_object_or_404(ProjectEstimation, pk=pk)
            serializer = EstimationSerializer(estimation)
        else:
            estimations = ProjectEstimation.objects.all()
            serializer = EstimationSerializer(estimations, many=True)
        return Response(serializer.data)


    
    def put(self, request, pk):
        estimation = get_object_or_404(ProjectEstimation, id=pk)
        serializer = EstimationSerializer(estimation, data=request.data, partial=True)
        if serializer.is_valid():
            estimation = serializer.save()

            # Trigger background tasks asynchronously
            recalculate_project_finances.delay(estimation.project.id)
            send_budget_alerts.delay(estimation.project.id)

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        estimation = get_object_or_404(ProjectEstimation, pk=pk)
        serializer = EstimationSerializer(estimation)
        return Response(serializer.data)


class ProfitLossAdvancedAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request, pk):
        data = calculate_project_profit_loss(pk)
        serializer = ProfitLossSerializer(instance=data)
        return Response(serializer.data)


class ProjectEstimationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    """
    Fetch latest estimation for a given project.
    """
    
    
    def get(self, request, pk, format=None):
        # Get all estimations for the project
        estimations = ProjectEstimation.objects.filter(project_id=pk)
        
        if not estimations.exists():
            return Response(
                {"error": "No estimation found for this project."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Serialize all estimations
        serializer = EstimationSerializer(estimations, many=True)
        # print(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ProjectEstimationChangeAPIView(APIView):
    
    def get(self, request, pk):
        project = get_object_or_404(Project, id=pk)
        estimation = ProjectEstimation.latest_estimation(project)

        if not estimation:
            return Response({"error": "No estimation found for this project."}, status=status.HTTP_404_NOT_FOUND)

        serializer = EstimationSerializer(estimation)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProjectPaymentTrackingAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    """
    Fetch all payment tracking and milestones for a given project.
    """

    def get(self, request, pk, format=None):
        try:
            payments = ProjectPaymentTracking.objects.filter(project_id=pk).order_by("-created_at")
            if not payments.exists():
                return Response({"error": "No payments found for this project."}, status=status.HTTP_404_NOT_FOUND)

            serializer = ProjectPaymentTrackingSerializer(payments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print("❌ ERROR:", e)
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   

# views.py
class ProjectEstimationPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        # latest estimation
        estimation = project.estimations.order_by("-version", "-created_at").first()
        est_data = None
        if estimation:
            est_data = {
                "id": estimation.id,
                "estimation_date": estimation.estimation_date,
                "initial_amount": estimation.initial_amount,
                "additional_amount": estimation.additional_amount,
                "total_amount": estimation.total_amount,
                "pending_amount": estimation.pending_amount,
                "received_amount": estimation.received_amount,
                "is_approved": estimation.is_approved,
                "purchase_order_status": estimation.purchase_order_status,
                "created_at": estimation.created_at,
            }

        # payments list
        payments = project.payments.all().order_by("-created_at")
        payment_list = []
        for p in payments:
            holds = []
            if hasattr(p, "holds"):
                for h in p.holds.all():
                    holds.append({
                        "id": h.id,
                        "amount": h.amount,
                        "is_active": h.is_active,
                        "created_at": h.created_at,
                        "released_at": h.released_at,
                    })

            payment_list.append({
                "id": p.id,
                "payment_type": p.payment_type,
                "approved_budget": p.approved_budget,
                "additional_amount": p.additional_amount,
                "payout": p.payout,
                "retention_amount": p.retention_amount,
                "penalty_amount": p.penalty_amount,
                "total_available_budget": p.total_available_budget,
                "total_milestones_amount": p.total_milestones_amount,
                "completed_milestones_amount": p.completed_milestones_amount,
                "total_holds_amount": p.total_holds_amount,
                "pending": p.pending,
                "budget_utilization_percentage": p.budget_utilization_percentage,
                "holds": holds,
                "created_at": p.created_at,
            })

        return Response({"estimation": est_data, "payments": payment_list}, status=status.HTTP_200_OK)


# Payment endpoints
class PaymentListCreateAPIView(APIView):
#
    def post(self, request):
        try:
            serializer = ProjectPaymentTrackingSerializer(data=request.data)
            if serializer.is_valid():
                project = serializer.validated_data.get("project")
                approved_budget = serializer.validated_data.get("approved_budget", Decimal("0.00"))

                # Validate against company policy
                validation = validate_payment_against_policy(project, approved_budget, user=request.user)
                if not validation["allowed"]:
                    return Response({"error": validation["message"]}, status=status.HTTP_400_BAD_REQUEST)

                # Save payment with adjusted budget
                payment = serializer.save(approved_budget=Decimal(validation["adjusted_amount"]))

                # Run background tasks
                BudgetMonitorService.monitor_project(project)
                recalculate_project_finances.delay(project.id)
                send_budget_alerts.delay(project.id)

                return Response(
                    {"message": validation["message"], "payment": ProjectPaymentTrackingSerializer(payment).data},
                    status=status.HTTP_201_CREATED
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, project_id, payment_id):
        """Update an existing payment record"""
        project = get_object_or_404(Project, id=project_id)
        payment = get_object_or_404(ProjectPaymentTracking, id=payment_id, project_id=project_id)
        data = request.data.copy()

        if "approved_budget" in data:
            try:
                approved_budget = Decimal(str(data.get("approved_budget", "0.00")))
            except Exception:
                return Response({"error": "approved_budget invalid"}, status=status.HTTP_400_BAD_REQUEST)

            validation = validate_payment_against_policy(project, approved_budget, user=request.user)
            if not validation["allowed"]:
                return Response({"error": validation["message"]}, status=status.HTTP_400_BAD_REQUEST)
            data["approved_budget"] = str(validation["adjusted_amount"])

        serializer = ProjectPaymentTrackingSerializer(payment, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Run sync monitor service + async background tasks
            BudgetMonitorService.monitor_project(project)
            recalculate_project_finances.delay(project_id)
            send_budget_alerts.delay(project_id)

            return Response({"message": "Updated", "payment": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete a payment record"""
        payment = get_object_or_404(ProjectPaymentTracking, pk=pk)
        payment.delete()
        return Response({"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

    def get(self, request, pk=None):
        """Get all or one payment"""
        if pk:
            payment = get_object_or_404(ProjectPaymentTracking, pk=pk)
            serializer = ProjectPaymentTrackingSerializer(payment)
            return Response(serializer.data)
        payments = ProjectPaymentTracking.objects.all()
        serializer = ProjectPaymentTrackingSerializer(payments, many=True)
        return Response(serializer.data)

from decimal import InvalidOperation
class AddHoldView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, pk):
        try:
            print("PK received:", pk)
            project = ProjectPaymentTracking.objects.get(id=pk)
            
            try:
                amount = Decimal(str(request.data.get("amount", "0.00")))
            except (InvalidOperation, TypeError):
                return Response({"error": "Invalid amount format"}, status=status.HTTP_400_BAD_REQUEST)

            if amount <= 0:
                return Response({"error": "Invalid hold amount"}, status=status.HTTP_400_BAD_REQUEST)

            # Check if hold exceeds pending budget
            active_holds_sum = project.holds.filter(is_active=True).aggregate(total=models.Sum('amount'))['total'] or Decimal("0.00")
            pending_budget = (
                project.total_available_budget
                - (project.payout or Decimal("0.00"))
                - active_holds_sum
                - (project.retention_amount or Decimal("0.00"))
                + (project.penalty_amount or Decimal("0.00"))
            )

            if amount > pending_budget:
                return Response({"error": "Hold amount exceeds pending budget"}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Correct field name here
            hold = Hold.objects.create(payment_tracking=project, amount=amount, is_active=True)
            serializer = HoldSerializer(hold)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print("ERROR:", e)
            traceback.print_exc()
            return Response({"error": "Internal server error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class ReleaseHoldView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]    

    def post(self, request, hold_id):
        try:
            hold = Hold.objects.get(id=hold_id, is_active=True)
        except Hold.DoesNotExist:
            return Response({"error": "Hold not found or already released"}, status=status.HTTP_404_NOT_FOUND)

        hold.is_active = False
        hold.released_at = timezone.now()
        hold.save()
        serializer = HoldSerializer(hold)
        return Response(serializer.data, status=status.HTTP_200_OK)
from django.db.models import Sum
class MilestoneListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]    

    def get(self, request):
        qs = ProjectPaymentMilestone.objects.select_related("payment_tracking").all()
        ser = ProjectPaymentMilestoneSerializer(qs, many=True)
        return Response(ser.data)

    def post(self, request):
        ser = ProjectPaymentMilestoneSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)

        payment = (
            ProjectPaymentTracking.objects.get(pk=ser.validated_data["payment_tracking"].id)
            if hasattr(ser.validated_data["payment_tracking"], "id")
            else ProjectPaymentTracking.objects.get(pk=ser.validated_data["payment_tracking"])
        )

        validated = ser.validated_data.copy()
        validated["payment_tracking"] = payment

        # ✅ create milestone
        milestone = create_milestone(validated, request.user, enforce_budget=True)

        # ✅ only add new milestone amount to existing payout
        payment.payout = (payment.payout or Decimal("0.00")) + milestone.amount
        payment.save(update_fields=["payout"])

        notify_milestone_update(milestone, [payment.created_by.email] if payment.created_by else [])

        return Response(ProjectPaymentMilestoneSerializer(milestone).data, status=status.HTTP_201_CREATED)


class MilestoneDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]    

    def get(self, request, pk):
        m = ProjectPaymentMilestone.objects.get(pk=pk)
        return Response(ProjectPaymentMilestoneSerializer(m).data)

   
    def put(self, request, pk):
        milestone = ProjectPaymentMilestone.objects.get(pk=pk)
        old_amount = milestone.amount

        milestone.status = request.data.get("status", milestone.status)
        milestone.notes = request.data.get("notes", milestone.notes)
        milestone.amount = Decimal(request.data.get("amount", milestone.amount))  # optional update
        milestone.save()

        # ✅ adjust payout difference
        diff = milestone.amount - old_amount
        payment = milestone.payment_tracking
        payment.payout = (payment.payout or Decimal("0.00")) + diff
        payment.save(update_fields=["payout"])

        notify_milestone_update(milestone)
        return Response({"msg": "Milestone updated"}, status=status.HTTP_200_OK)


    def delete(self, request, pk):
        ProjectPaymentMilestone.objects.get(pk=pk).delete()
        return Response({"detail": "Deleted"}, status=status.HTTP_204_NO_CONTENT)


# Transactions
class TransactionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]    

    def post(self, request):
        ser = PaymentTransactionSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        payment_id = ser.validated_data["payment_tracking"].id if hasattr(ser.validated_data["payment_tracking"], "id") else ser.validated_data["payment_tracking"]
        tx = create_transaction(payment_id, ser.validated_data["amount"], request.user, method=ser.validated_data.get("method"), notes=ser.validated_data.get("notes"))
        payment = ProjectPaymentTracking.objects.get(pk=payment_id)
        # If budget breach after transaction, notify
        if payment.is_budget_exceeded:
            notify_budget_breach(payment, [payment.created_by.email] if payment.created_by else [])
        return Response(PaymentTransactionSerializer(tx).data, status=status.HTTP_201_CREATED)



class ChangeRequestAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(requested_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, pk=None):
        if pk:
            cr = get_object_or_404(ChangeRequest, pk=pk)
            serializer = ChangeRequestSerializer(cr)
            return Response(serializer.data)
        crs = ChangeRequest.objects.all()
        serializer = ChangeRequestSerializer(crs, many=True)
        return Response(serializer.data)

    def put(self, request, pk):
        cr = get_object_or_404(ChangeRequest, pk=pk)
        serializer = ChangeRequestSerializer(cr, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        cr = get_object_or_404(ChangeRequest, pk=pk)
        cr.delete()
        return Response({"message": "Deleted"}, status=status.HTTP_204_NO_CONTENT)


class ChangeRequestApprovalAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, action):
        cr = get_object_or_404(ChangeRequest, pk=pk)

        if not request.user.is_staff:
            return Response({"error": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            if action == "approve":
                cr.approve(request.user)
                return Response({"detail": f"ChangeRequest {cr.id} approved"}, status=status.HTTP_200_OK)
            elif action == "reject":
                cr.reject(request.user)
                return Response({"detail": f"ChangeRequest {cr.id} rejected"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



# Additional budget (requests & approvals)
class AdditionalRequestListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        qs = AdditionalBudgetRequest.objects.select_related("payment_tracking").all()
        ser = AdditionalBudgetRequestSerializer(qs, many=True)
        return Response(ser.data)


    def post(self, request):
        # create budget request
        req = AdditionalBudgetRequest.objects.create(
            payment_tracking_id=request.data["payment_tracking"],
            requested_amount=request.data["requested_amount"],
            reason=request.data.get("reason", ""),
            created_by=request.user,
        )
        # send email
        notify_budget_request(req)
        return Response({"msg": "Budget request created"}, status=status.HTTP_201_CREATED)
   

class AdditionalRequestApproveAPIView(APIView):
    permission_classes = [IsAuthenticated, IsFinanceApprover]
    authentication_classes = [JWTAuthentication]    


    def post(self, request, req_id, *args, **kwargs):
        try:
            additional_request = AdditionalBudgetRequest.objects.get(id=req_id)

            if additional_request.status != AdditionalBudgetRequest.STATUS_PENDING:
                return Response({"error": "Request is already processed"}, status=400)

            # Approve the request
            additional_request.status = AdditionalBudgetRequest.STATUS_APPROVED
            additional_request.approved_by = request.user
            additional_request.approved_at = timezone.now()
            additional_request.approval_notes = request.data.get("approval_notes", "")
            additional_request.save()

            # Update only the additional_amount
            payment = additional_request.payment_tracking
            payment.additional_amount += additional_request.requested_amount
            payment.save()  # total_available_budget is automatically updated via the property

            return Response({"message": "Request approved successfully"})
        except AdditionalBudgetRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=404)


# views.py
class ChangeRequestCreateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, pk):
        """Create a new Change Request for a project"""
        project = get_object_or_404(Project, id=pk)
        data = request.data.copy()
        data["project"] = project.id
        data["requested_by"] = request.user.id

        serializer = ChangeRequestSerializer(data=data)
        if serializer.is_valid():
            cr = serializer.save()
            return Response(ChangeRequestSerializer(cr).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangeRequestApproveView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, pk):
        cr = get_object_or_404(ChangeRequest, id=pk)
        action = request.data.get("status")  # 'Approved' or 'Received'

        try:
            if action == "Approved":
                cr.approve(reviewer_user=request.user)
                return Response({"message": "Change Request approved successfully."}, status=status.HTTP_200_OK)

            elif action == "Received":
                updated_estimation = cr.mark_received(reviewer_user=request.user)
                serializer = EstimationSerializer(updated_estimation)
                return Response(serializer.data, status=status.HTTP_200_OK)

            else:
                return Response({"error": "Invalid action. Must be 'Approved' or 'Received'."}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
   


class ChangeRequestListView(APIView): 
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, pk):
        change_requests = ChangeRequest.objects.filter(project_id=pk).order_by("-created_at")
        serializer = ChangeRequestSerializer(change_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangeRequestRejectView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, pk):
        """
        Reject a Change Request
        """
        cr = get_object_or_404(ChangeRequest, id=pk)
        try:
            cr.reject(request.user)
            return Response({"detail": f"ChangeRequest {cr.id} rejected"}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        qs = Notification.objects.filter(recipient=request.user)
        ser = NotificationSerializer(qs, many=True)
        return Response(ser.data)


class RuleListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]  # add role-based permission for admin in production
    authentication_classes = [JWTAuthentication]    

    def get(self, request):
        qs = Rule.objects.all()
        ser = RuleSerializer(qs, many=True)
        return Response(ser.data)

    def post(self, request):
        ser = RuleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        r = ser.save()
        return Response(RuleSerializer(r).data, status=status.HTTP_201_CREATED)






class InvoiceGenerateAPIView(APIView):
    """Generate Invoice dynamically based on Estimation & Payments"""

    def post(self, request, pk):
        try:
            project = Project.objects.get(id=pk)
            estimation = ProjectEstimation.objects.filter(project=project).latest("version")

            # Unique Invoice Number
            invoice_number = f"INV-{now().year}-{project.id}-{uuid.uuid4().hex[:6].upper()}"

            # Dates
            invoice_date = now().date()
            due_days = request.data.get("due_days", 30)
            due_date = invoice_date + timedelta(days=due_days)

            # Financials
            total_amount = estimation.total_amount
            received_amount = estimation.received_amount
            pending_amount = estimation.pending_amount
            status_label = "Paid" if pending_amount == Decimal("0.00") else "Unpaid"

            # Save Invoice
            invoice = Invoice.objects.create(
                project=project,
                estimation=estimation,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                due_date=due_date,
                amount=total_amount,
                status=status_label,
                notes=request.data.get("notes", "")
            )

            # Generate PDF
            pdf_path = os.path.join(settings.MEDIA_ROOT, "invoices", f"{invoice_number}.pdf")
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

            c = canvas.Canvas(pdf_path, pagesize=A4)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, 800, f"Invoice: {invoice_number}")
            c.setFont("Helvetica", 12)
            c.drawString(50, 780, f"Project: {project.project_name}")
            c.drawString(50, 760, f"Client: {getattr(project.client, 'name', 'Unknown')}")
            c.drawString(50, 740, f"Invoice Date: {invoice_date}")
            c.drawString(50, 720, f"Due Date: {due_date}")
            c.drawString(50, 700, f"Total: {total_amount}")
            c.drawString(50, 680, f"Received: {received_amount}")
            c.drawString(50, 660, f"Pending: {pending_amount}")
            c.drawString(50, 640, f"Status: {status_label}")
            c.save()

            invoice.pdf_file.name = f"invoices/{invoice_number}.pdf"
            invoice.save()

            return Response(InvoiceSerializer(invoice, context={"request": request}).data, status=status.HTTP_201_CREATED)

        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        except ProjectEstimation.DoesNotExist:
            return Response({"error": "No estimation found for project"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def download_invoice(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, 'invoices', filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    else:
        raise Http404("Invoice not found")