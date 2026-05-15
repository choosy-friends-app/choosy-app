from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Max
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from core.models import Group, PlanProposal, Plan, GroupMember
from core.forms import GroupForm, PlanProposalForm, PlanForm


class OwnerRequiredMixin(UserPassesTestMixin):
    raise_exception = True

    owner_field = "created_by"

    def test_func(self):
        obj = self.get_object()
        return getattr(obj, self.owner_field) == self.request.user

class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'pages/crear_entidad.html'
    success_url = reverse_lazy('groups')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        # Add the owner as an active member with OWNER role
        self.object.add_member(user=self.request.user, role=GroupMember.Role.OWNER)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Group'
        context['meta_title'] = 'Create Group'
        return context

class PlanProposalCreateView(LoginRequiredMixin, CreateView):
    model = PlanProposal
    form_class = PlanProposalForm
    template_name = 'pages/crear_entidad.html'
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Plan Proposal'
        context['meta_title'] = 'Create Proposal'
        return context

class PlanCreateView(LoginRequiredMixin, CreateView):
    model = Plan
    form_class = PlanForm
    template_name = 'pages/plan_form.html'
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        proposal_id = self.request.GET.get("proposal")
        if proposal_id:
            proposal = PlanProposal.objects.filter(id=proposal_id, created_by=self.request.user).first()
            if proposal is not None:
                initial["proposal"] = proposal
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # Automatically set the group from the proposal
        form.instance.group = form.instance.proposal.group
        max_order = Plan.objects.filter(proposal=form.instance.proposal).aggregate(Max("option_order"))["option_order__max"]
        form.instance.option_order = 0 if max_order is None else max_order + 1
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Plan Option'
        context['meta_title'] = 'Create Plan'
        return context

class GroupUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'pages/crear_entidad.html'
    success_url = reverse_lazy('groups')
    owner_field = "owner"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Group: {self.get_object().name}'
        context['meta_title'] = 'Edit Group'
        return context

class PlanProposalUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = PlanProposal
    form_class = PlanProposalForm
    template_name = 'pages/crear_entidad.html'
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Proposal: {self.get_object().title}'
        context['meta_title'] = 'Edit Proposal'
        return context

class PlanUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Plan
    form_class = PlanForm
    template_name = 'pages/plan_form.html'
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.group = form.instance.proposal.group
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Plan: {self.get_object().title}'
        context['meta_title'] = 'Edit Plan'
        return context

class GroupDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Group
    template_name = 'pages/confirmar_borrado.html'
    success_url = reverse_lazy('groups')
    owner_field = "owner"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Group'
        context['meta_title'] = 'Delete Group'
        return context

class PlanProposalDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = PlanProposal
    template_name = 'pages/confirmar_borrado.html'
    success_url = reverse_lazy('dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Proposal'
        context['meta_title'] = 'Delete Proposal'
        return context

class PlanDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Plan
    template_name = 'pages/confirmar_borrado.html'
    success_url = reverse_lazy('dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Plan'
        context['meta_title'] = 'Delete Plan'
        return context
