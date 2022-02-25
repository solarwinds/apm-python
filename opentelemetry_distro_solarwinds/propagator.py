import typing

from opentelemetry.context.context import Context
from opentelemetry.propagators import textmap

class SolarWindsFormat(textmap.TextMapPropagator):

    def extract(
        self,
        carrier: textmap.CarrierT,
        context: typing.Optional[Context] = None,
        getter: textmap.Getter = textmap.default_getter,
    ) -> Context:
        """
        Extracts from carrier into SpanContext
        """
        if context is None:
            context = Context()
        return context

    def inject(
        self,
        carrier: textmap.CarrierT,
        context: typing.Optional[Context] = None,
        setter: textmap.Setter = textmap.default_setter,
    ) -> None:
        """
        Injects from SpanContext into carrier
        """
        pass

    @property
    def fields(self) -> typing.Set[str]:
        """
        Returns a set with the fields set in `inject`
        """
        return {'foo', 'bar'}
