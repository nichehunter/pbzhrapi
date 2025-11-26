from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import register_events, register_job
from django_apscheduler.models import DjangoJobExecution
from datetime import datetime, date, timedelta
from django.db.models import Sum
from calendar import monthrange
from decimal import Decimal
from django.db import transaction, IntegrityError
from collections import defaultdict
from apscheduler.schedulers.background import BackgroundScheduler

from scheduler.models import *
from payroll.models import *


def GenerateMonthAllowance():
	lock = None
	try:
		with transaction.atomic():
			lock, created = JobLock.objects.get_or_create(
				name="GeneratePayedPensioner",
				defaults={"locked_until": now() + timedelta(minutes=10)}
			)
			if not created and lock.locked_until > now():
				print("⛔ JobLock active — skipping run")
				return
			lock.locked_until = now() + timedelta(minutes=10)
			lock.save()
	except IntegrityError:
		print("⛔ JobLock already exists — skipping")
		return

	try:
		today = datetime.date.today()
		# day = CalculationDay.objects.filter(date=int(today.day), is_active=True)
		day = CalculationDay.objects.filter(date=16, is_active=True)
		if day.exists():
			allowances = StaffAllowance.objects.all()

			# Wrap everything inside a single atomic block
			with transaction.atomic():
				for al in allowances:
					obj, created = MonthlyAllowance.objects.get_or_create(
						month=today.month,
						year=today.year,
						allowance=al.allowance,
						staff=al.staff,
						defaults={
							"amount": al.amount,
							"is_active": True,
							"recorded_by": 1,
							"date": today,
							"month_consumed": 0,
						}
					)

					print(f"{'Created' if created else 'Already exists'} allowance for {al.staff}")
	
		else:
			print("⛔ No active calculation today")

	except Exception as e:
		print("\n🔥 CRITICAL ERROR in GenerateMonthAllowance()")
		print(str(e))
		import traceback
		traceback.print_exc()

	finally:
		if lock:
			lock.delete()
		print("🔓 JobLock released")



def GenerateMonthDeduction():
    lock = None
    try:
        with transaction.atomic():
            lock, created = JobLock.objects.get_or_create(
                name="GenerateMonthDeduction",
                defaults={"locked_until": now() + timedelta(minutes=10)}
            )
            if not created and lock.locked_until > now():
                print("⛔ JobLock active — skipping run")
                return
            # Extend lock for 10 more minutes
            lock.locked_until = now() + timedelta(minutes=10)
            lock.save()
    except IntegrityError:
        print("⛔ JobLock already exists — skipping")
        return

    try:
        today = datetime.date.today()

        day = CalculationDay.objects.filter(date=16, is_active=True)

        if day.exists():

            staff_deductions = StaffDeduction.objects.filter(is_active=True)

            with transaction.atomic():
                for sd in staff_deductions:

                    # Determine monthly deduction amount
                    if sd.is_percentage:
                        try:
                            salary = StaffSalary.objects.get(staff=sd.staff)
                            deduction_amount = salary.amount * sd.percentage
                        except StaffSalary.DoesNotExist:
                            deduction_amount = 0
                    else:
                        deduction_amount = sd.amount

                    # Reduce balance by deduction_amount
                    new_balance = sd.balance - deduction_amount

                    # Prevent negative balance
                    if new_balance <= 0:
                        deduction_amount = sd.balance  # take remaining balance
                        new_balance = 0
                        sd.is_active = False  # deactivate since balance finished
                        print(f"✅ Deduction finished for {sd.staff.full_name}, balance is now 0")
                    else:
                        sd.is_active = True

                    sd.balance = new_balance
                    sd.save(update_fields=['balance', 'is_active'])

                    # Only create MonthlyDeduction if deduction_amount > 0
                    if deduction_amount > 0:
                        md, created = MonthlyDeduction.objects.get_or_create(
                            staff=sd.staff,
                            deduction=sd.deduction,
                            date=today,
                            defaults={
                                "amount": deduction_amount,
                                "month": today.month,
                                "year": today.year,
                                "month_consumed": 0,
                                "is_active": True,
                                "recorded_by": 1
                            }
                        )
                        print(f"{'Created' if created else 'Already exists'} deduction for {sd.staff.full_name}: {deduction_amount}")

        else:
            print("⛔ No active calculation today")

    except Exception as e:
        import traceback
        print("🔥 CRITICAL ERROR in GenerateMonthDeduction()")
        print(str(e))
        traceback.print_exc()

    finally:
        if lock:
            lock.delete()
            print("🔓 JobLock released")





def GenerateMonthOrganizationContribution():
    lock = None
    try:
        with transaction.atomic():
            lock, created = JobLock.objects.get_or_create(
                name="GenerateMonthOrganizationContribution",
                defaults={"locked_until": now() + timedelta(minutes=10)}
            )
            if not created and lock.locked_until > now():
                print("⛔ JobLock active — skipping run")
                return

            # Extend lock
            lock.locked_until = now() + timedelta(minutes=10)
            lock.save()

    except IntegrityError:
        print("⛔ JobLock already exists — skipping")
        return

    try:
        today = datetime.date.today()

        day = CalculationDay.objects.filter(date=16, is_active=True)

        if not day.exists():
            print("⛔ No active calculation today — skipping")
            return

        staff_orgs = StaffOrganization.objects.filter(is_active=True)

        try:
            deduction_type = Deduction.objects.get(name="organization")
        except Deduction.DoesNotExist:
            print("❌ Deduction type 'organization' not found")
            return

        with transaction.atomic():
            for so in staff_orgs:

                # ----------- Determine monthly contribution -------------
                if so.is_percentage:
                    try:
                        salary = StaffSalary.objects.get(staff=so.staff)
                        contribution_amount = salary.amount * so.percentage
                    except StaffSalary.DoesNotExist:
                        contribution_amount = 0
                else:
                    contribution_amount = so.amount

                if contribution_amount <= 0:
                    print(f"⚠️ Skipping {so.staff.full_name}: contribution amount = 0")
                    continue

                # ----------- Update balance (balance += contribution) ------------
                new_balance = so.balance + contribution_amount
                so.balance = new_balance
                so.save(update_fields=['balance'])

                # ----------- Avoid duplicate monthly records ----------
                exists = MonthlyDeduction.objects.filter(
                    staff=so.staff,
                    deduction=deduction_type,
                    organization=so.organization,
                    month=today.month,
                    year=today.year
                ).exists()

                if exists:
                    print(f"🟡 Monthly organization contribution already exists for {so.staff.full_name}")
                    continue

                # ----------- Create MonthlyDeduction -------------------
                MonthlyDeduction.objects.create(
                    staff=so.staff,
                    deduction=deduction_type,
                    organization=so.organization,
                    amount=contribution_amount,
                    month=today.month,
                    year=today.year,
                    month_consumed=0,
                    is_active=True,
                    recorded_by=1,
                    date=today
                )

                print(f"✅ Contribution saved for {so.staff.full_name}: {contribution_amount}")

    except Exception as e:
        import traceback
        print("\n🔥 CRITICAL ERROR in GenerateMonthOrganizationContribution()")
        print(str(e))
        traceback.print_exc()

    finally:
        if lock:
            lock.delete()
            print("🔓 JobLock released")






