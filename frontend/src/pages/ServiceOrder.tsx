import React, { useEffect, useState } from 'react';
import Header from '../components/Header';
import ServiceStep from '../components/ServiceStep';
import { useParams } from 'react-router-dom';
interface ManutencaoMaquina {
  _id: string;
  ordem_servico: Ordemserv[];
}

interface Ordemserv {
  problema: string;
  equipamentos_necessarios: Equipamento[];
  passos: Passo[];
  observacoes: string[];
  referencias: string[];
}

interface Equipamento {
  nome: string;
  sap_code: string;
  quantidade: number;
}

interface Passo {
  ordem: number;
  duracao: string;
  descricao: string;
  justificativa: string;
  medidas_seguranca: string[];
}

function ServiceOrder() {
  const { id } = useParams<string>();
  const [data, setdata] = useState<ManutencaoMaquina>();
  useEffect(() => {
    const fetchData = async () => {
      const data = await fetch(`http://localhost:8000/service/${id}`);
      const datajs = await data.json();
      setdata(datajs);
      console.log(datajs);
    };
    fetchData()
      // make sure to catch any error
      .catch(console.error);
  }, []);
  return (
    <>
      <Header />
      {data?.ordem_servico[0].passos.map((step) => (
        <ServiceStep
          time={`${step.duracao}`}
          number={step.ordem}
          title={step.descricao}
          description={step.justificativa}
        ></ServiceStep>
      ))}
    </>
  );
}

export default ServiceOrder;
